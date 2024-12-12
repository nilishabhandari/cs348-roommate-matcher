from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Profile
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///roommates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    # Setting the isolation level for transactions
    'isolation_level': 'SERIALIZABLE'
}
app.secret_key = 'supersecretkey'
db.init_app(app)

# Ensure database tables are created before the first request
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    profiles = Profile.query.all()  # ORM query
    return render_template('index.html', profiles=profiles)

@app.route('/add_profile', methods=['GET', 'POST'])
def add_profile():
    session = db.session
    if request.method == 'POST':
        try:
            session.begin()  # Begin transaction

            username = request.form['username']
            email = request.form['email']
            school_year = request.form['school_year']
            residence = request.form['residence']
            gender = request.form['gender']
            smoker = 'smoker' in request.form
            preferred_gender = request.form['preferred_gender']

            profile = Profile(
                username=username,
                email=email,
                password_hash='hashed_password',
                school_year=school_year,
                residence=residence,
                gender=gender,
                smoker=smoker,
                preferred_gender=preferred_gender
            )
            session.add(profile)  # Add profile to the transaction
            session.commit()  # Commit transaction
            flash(f"Added {username} to directory!", "success")
            return redirect(url_for('home'))

        except SQLAlchemyError as e:
            session.rollback()  # Rollback transaction if error
            flash(f"Error adding profile: {str(e)}", "error")
            return redirect(url_for('add_profile'))

    return render_template('add_profile.html')

@app.route('/edit_profile/<int:profile_id>', methods=['GET', 'POST'])
def edit_profile(profile_id):
    session = db.session
    profile = Profile.query.get_or_404(profile_id)

    if request.method == 'POST':
        try:
            profile.school_year = request.form['school_year']
            profile.residence = request.form['residence']
            profile.gender = request.form['gender']
            profile.preferred_gender = request.form['preferred_gender']
            profile.smoker = 'smoker' in request.form

            db.session.commit()  # Commit the changes to the database
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('home'))

        except SQLAlchemyError as e:
            session.rollback()  # Rollback transaction if error
            flash(f"Error updating profile: {str(e)}", "error")

    residence_halls = db.session.query(Profile.residence).distinct().all()
    residence_halls = [hall[0] for hall in residence_halls] 

    return render_template('edit_profile.html', profile=profile, residence_halls=residence_halls)

@app.route('/delete_profile/<int:profile_id>', methods=['POST'])
def delete_profile(profile_id):
    session = db.session
    try:
        session.begin()  # Begin transaction

        sql_delete = text("DELETE FROM profile WHERE profile_id = :profile_id")
        session.execute(sql_delete, {'profile_id': profile_id})

        session.commit()  # Commit transaction
        flash("Profile deleted successfully!", "success")

    except SQLAlchemyError as e:
        session.rollback()  # Rollback transaction if error
        flash(f"Error deleting profile: {str(e)}", "error")

    finally:
        session.close()  # Close the session

    return redirect(url_for('home'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        gender = request.form['gender']
        ok_with_smoker = 'ok_with_smoker' in request.form
        preferred_residence = request.form['residence']

        sql_query = text("""
            SELECT * FROM profile
            WHERE (:gender IS NULL OR preferred_gender = :gender)
            AND (:preferred_residence IS NULL OR residence = :preferred_residence)
            AND (:ok_with_smoker = 1 OR smoker = 0)
        """)

        results = db.session.execute(sql_query, {
            'gender': gender if gender else None,
            'preferred_residence': preferred_residence if preferred_residence else None,
            'ok_with_smoker': 1 if ok_with_smoker else 0
        }).fetchall()

        return render_template('search_results.html', results=results)

    return render_template('search.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    results = []
    num_smokers = 0
    num_females = 0
    num_males = 0
    residences = []

    residences_query = Profile.query.with_entities(Profile.residence).distinct()
    residences = [residence[0] for residence in residences_query]

    if request.method == 'POST':
        gender = request.form['gender']
        residence = request.form['residence']
        
        sql_query = text("""
            SELECT * FROM profile 
            WHERE (:gender IS NULL OR gender = :gender)
            AND (:residence IS NULL OR residence = :residence)
            AND (:is_smoker IS NULL OR smoker = :is_smoker)
        """)

        results = db.session.execute(sql_query, {
            'gender': gender,
            'residence': residence,
            'is_smoker': request.form.get('is_smoker')
        }).fetchall()

        num_smokers = sum(1 for profile in results if profile.smoker)
        num_females = sum(1 for profile in results if profile.gender == 'Female')
        num_males = sum(1 for profile in results if profile.gender == 'Male')

    return render_template(
        'report.html',
        results=results,
        num_smokers=num_smokers,
        num_females=num_females,
        num_males=num_males,
        residences=residences
    )

if __name__ == '__main__':
    app.run(debug=True)
