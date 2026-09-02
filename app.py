from flask import Flask, request, redirect, render_template, session
import mysql.connector
import time
import joblib   # ✅ ML import
import requests

app = Flask(__name__)
app.secret_key = "secret123"

# ================== LOAD ML MODEL ==================
model = joblib.load('model.pkl')   # ✅ load trained model

# ================== DATABASE CONNECTION ==================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dbms123",
    database="career_db"
)
cursor = db.cursor()

# ================== QUESTIONS ==================
questions = [
    {
        "question": "If all cats are animals and some animals are pets, which statement is correct?",
        "options": ["All cats are pets", "Some cats are not pets", "Some animals are cats", "All animals are cats"],
        "answer": "Some animals are cats"
    },
    {
        "question": "A train travels 60 km in 1 hour 30 minutes. What is its average speed?",
        "options": ["40 km/h", "50 km/h", "60 km/h", "45 km/h"],
        "answer": "40 km/h"
    },
    {
        "question": "Find the next number: 2, 6, 12, 20, 30...",
        "options": ["36", "40", "42", "50"],
        "answer": "42"
    },
    {
        "question": "Output of Python code: [x**2 for x in numbers if x%2==0]",
        "options": ["[1,4,9,16]", "[2,4]", "[4,16]", "[1,9]"],
        "answer": "[4,16]"
    },
    {
        "question": "Correct way to define function in Python?",
        "options": ["function myFunc()", "def myFunc()", "func myFunc()", "define myFunc()"],
        "answer": "def myFunc()"
    },
    {
        "question": "Output of print(type(3/2))?",
        "options": ["int", "float", "str", "bool"],
        "answer": "float"
    },
    {
        "question": "Example of supervised learning?",
        "options": ["K-Means", "Linear Regression", "PCA", "Association Rules"],
        "answer": "Linear Regression"
    },
    {
        "question": "Overfitting occurs when?",
        "options": ["Good train, bad test", "Bad both", "Ignore data", "Good all"],
        "answer": "Good train, bad test"
    },
    {
        "question": "NLP stands for?",
        "options": ["Natural Logic", "Neural Language", "Natural Language Processing", "Non-linear Programming"],
        "answer": "Natural Language Processing"
    },
    {
        "question": "Which skill do you enjoy?",
        "options": ["Programming", "Designing", "Data Analysis", "Communication"],
        "answer": None
    }
]

# ================== HOME ==================
@app.route('/')
def home():
     return render_template('index.html')

# ================== SIGNUP ==================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        db.commit()

        # ✅ Show success page instead of redirect
        return render_template('signup_success.html')

    return render_template('signup.html')
# ================== LOGIN ==================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None   # 👈 store error message

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        result = cursor.fetchone()

        if result:
            session['username'] = username
            session['score'] = 0
            session['answers'] = []
            return redirect('/exam')
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)
#====================JOBS===============
@app.route('/jobs')
def jobs_page():
    jobs = session.get('jobs', [])
    score = session.get('score', 0)
    branch = session.get('branch', '')

    return render_template('jobs.html', jobs=jobs, score=score, branch=branch)
# ================== EXAM ==================
@app.route('/exam')
def exam():
    session['start_time'] = time.time()
    return render_template('select_branch.html')

# ================== QUESTION ==================
@app.route('/question/<int:qno>', methods=['GET', 'POST'])
def question(qno):
    if 'branch' not in session:
        return redirect('/select_branch')

    branch = session['branch']

    # Fetch all questions for this branch
    cursor.execute("SELECT * FROM questions WHERE branch=%s", (branch,))
    questions = cursor.fetchall()

    total_time = 10 * 60  # total time in seconds

    start_time = session.get('start_time', time.time())
    session['start_time'] = start_time  # initialize if not exists
    elapsed = time.time() - start_time

    if elapsed > total_time:
        return redirect('/result')

    if qno >= len(questions):
        return redirect('/result')

    if request.method == 'POST':
        selected = request.form.get('answer')
        if selected:
            answers = session.get('answers', [])
            answers.append(selected)
            session['answers'] = answers

            correct = questions[qno][6]  # assuming column 6 is correct answer
            if correct is not None and selected.strip().lower() == correct.strip().lower():
                session['score'] = session.get('score', 0) + 10

        return redirect(f'/question/{qno + 1}')

    remaining = int(total_time - elapsed)

    return render_template(
        'question.html',
        q=questions[qno],
        qno=qno + 1,
        remaining=remaining
    )

## ================== RESULT (ML) ==================
@app.route('/result')
def result():
    score = session.get('score', 0)
    branch = session.get('branch', 'CSE')

    # ================= BRANCH-BASED CAREER MAPPING =================
    career_map = {
        'CSE': [
            (8, "Software Developer 💻"),
            (5, "Web Developer 🌐"),
            (0, "IT Support Engineer 🖥️")
        ],
        'ECE': [
            (8, "Embedded Systems Engineer 🔌"),
            (5, "VLSI Design Engineer 🔬"),
            (0, "Telecommunications Engineer 📡")
        ],
        'EEE': [
            (8, "Electrical Design Engineer ⚡"),
            (5, "Power Systems Engineer 🔋"),
            (0, "Electrical Technician 🔧")
        ],
        'MECH': [
            (8, "Mechanical Design Engineer ⚙️"),
            (5, "Production Engineer 🏭"),
            (0, "Maintenance Engineer 🔩")
        ],
        'CIVIL': [
            (8, "Structural Engineer 🏗️"),
            (5, "Site Engineer 🏛️"),
            (0, "Survey Engineer 📐")
        ],
        'MME': [
            (8, "Materials Research Engineer 🔬"),
            (5, "Quality Control Engineer ✅"),
            (0, "Metallurgical Technician ⚗️")
        ],
    }

    # Pick career based on branch + score
    career = "Engineer"
    for min_score, career_name in career_map.get(branch, career_map['CSE']):
        if score >= min_score:
            career = career_name
            break

    # ================= JOB API =================
    jobs = []
    try:
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

        # Clean emojis from career title for API query
        query = career.encode('ascii', 'ignore').decode().strip()

        params = {
            "app_id": "a5b3735a",
            "app_key": "e389d54f755181d0a04ff53e7b28cb61",
            "results_per_page": 5,
            "what": query
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data_json = response.json()

        for job in data_json.get('results', []):
            jobs.append({
                "title": job.get('title'),
                "company": job.get('company', {}).get('display_name'),
                "location": job.get('location', {}).get('display_name'),
                "description": job.get('description'),
                "link": job.get('redirect_url')
            })

    except requests.exceptions.RequestException as e:
        print("Error calling Adzuna API:", e)
    except ValueError as e:
        print("Invalid JSON:", e)

    # ================= SMART FEEDBACK =================
    improvement = ""

    if score >= 8:
        improvement = "🎉 Excellent performance! You have strong subject knowledge."
    elif score >= 5:
        improvement += f"🔹 Good effort! Revise core {branch} subjects to score higher."
    elif score >= 3:
        improvement += f"🔹 Keep practicing! Focus on fundamental {branch} concepts."
    else:
        improvement += f"🔹 Review your {branch} basics thoroughly and attempt again."

    motivation = "🚀 Keep learning and growing every day!"

    # ✅ Store jobs in session
    session['jobs'] = jobs

    return render_template(
        'result.html',
        score=score,
        career=career,
        branch=branch,
        improvement=improvement,
        motivation=motivation,
        jobs=jobs
    )
#=================JOB_DETAILS.HTML==========
@app.route('/job/<int:job_id>')
def job_details(job_id):
    jobs = session.get('jobs', [])

    if job_id >= len(jobs):
        return "Job not found ❌"

    job = jobs[job_id]

    return render_template('job_details.html', job=job, job_id=job_id)
#=================SAVED_JOBES================
@app.route('/save_job/<int:job_id>')
def save_job(job_id):
    if 'username' not in session:
        return redirect('/login')

    jobs = session.get('jobs', [])
    username = session.get('username')

    if job_id >= len(jobs):
        return redirect('/jobs')

    job = jobs[job_id]

    # جلوگیریduplicate
    cursor.execute(
        "SELECT * FROM saved_jobs WHERE username=%s AND title=%s",
        (username, job['title'])
    )
    existing = cursor.fetchone()

    if existing:
        return "⚠️ Job already saved!"

    cursor.execute(
        "INSERT INTO saved_jobs (username, title, company, location, link) VALUES (%s, %s, %s, %s, %s)",
        (username, job['title'], job['company'], job['location'], job['link'])
    )
    db.commit()

    return redirect(f"/job/{job_id}")
#==================SAVED JOBS============
#==================SAVED JOBS============
@app.route('/saved_jobs')
def saved_jobs():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    cursor.execute(
    "SELECT id, title, company, location, link FROM saved_jobs WHERE username=%s",
    (username,)
)
    jobs = cursor.fetchall()

    return render_template('saved_jobs.html', jobs=jobs)
# ================== LOGOUT ==================
# ================== LOGOUT ==================
@app.route('/logout')
def user_logout():  # <--- Change name to user_logout
    session.clear() 
    return redirect('/')  # <--- Redirect to the root path
# ================== DELETE JOB ==================
@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'username' not in session:
        return redirect('/login')

    cursor.execute(
        "DELETE FROM saved_jobs WHERE id=%s AND username=%s",
        (job_id, session['username'])
    )
    db.commit()

    return redirect('/saved_jobs')
#===================admin1=================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # simple admin check (you can improve later)
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect('/admin_dashboard')
        else:
            return "Invalid Admin Login"

    return render_template('admin_login.html')
#=====================admin2=============
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    # Users
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    # Saved Jobs
    cursor.execute("SELECT username, title, company FROM saved_jobs")
    saved_jobs = cursor.fetchall()

    # Applications (Pending)
    cursor.execute("SELECT id, username, job_title, company FROM applications WHERE status='pending'")
    pending_apps = cursor.fetchall()

    # Applications (Approved)
    cursor.execute("SELECT id, username, job_title, company FROM applications WHERE status='approved'")
    approved_apps = cursor.fetchall()

    return render_template(
        'admin_dashboard.html',
        users=users,
        saved_jobs=saved_jobs,
        pending_apps=pending_apps,
        approved_apps=approved_apps
    )
#=======================admin3=============
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'admin' not in session:
        return redirect('/admin')

    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()

    return redirect('/admin_dashboard')
#===================admin4============
#===================admin4============

@app.route('/admin_logout')
def admin_logout(): # <--- This can stay 'admin_logout'
    session.pop('admin', None)
    return redirect('/admin')



#===================================
@app.route('/view_user_jobs/<username>')
def view_user_jobs(username):
    if 'admin' not in session:
        return redirect('/admin')

    cursor.execute(
        "SELECT id, title, company, location, link FROM saved_jobs WHERE username=%s",
        (username,)
    )
    jobs = cursor.fetchall()

    return render_template("saved_jobs.html", jobs=jobs)
#====================BRANCH SELECTION===============
@app.route('/select_branch', methods=['GET', 'POST'])
def select_branch():
    if request.method == 'POST':
        branch = request.form['branch']
        session['branch'] = branch
        return redirect('/test')
    return render_template('select_branch.html')
#========================Fetch Questions Based on Branch===============
@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'branch' not in session:
        return redirect('/select_branch')

    branch = session['branch']

    cursor.execute("SELECT * FROM questions WHERE branch=%s", (branch,))
    questions = cursor.fetchall()

    return render_template('display_questions_test.html', questions=questions)
#=================EVALUATE ANSWERS===============
@app.route('/submit_test', methods=['POST'])
def submit_test():
    branch = session.get('branch', 'CSE')

    cursor.execute("SELECT * FROM questions WHERE branch=%s", (branch,))
    questions = cursor.fetchall()

    score = 0
    for q in questions:
        user_ans = request.form.get(f"q{q[0]}")
        if user_ans and user_ans == q[6]:
            score += 1

    session['score'] = score
    return redirect('/result')
#=====================APPLY ===================
#================== APPLY ==================
@app.route('/apply', methods=['POST'])
def apply():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']
    title = request.form['title']
    company = request.form['company']

    cursor.execute(
        "INSERT INTO applications (username, job_title, company, status) VALUES (%s, %s, %s, 'pending')",
        (username, title, company)
    )
    db.commit()

    return render_template('apply_success.html', title=title, company=company)
#==============ADMIN ROUTE===================
@app.route('/approve/<int:id>')
def approve(id):
    if 'admin' not in session:
        return redirect('/admin')

    cursor.execute("UPDATE applications SET status='approved' WHERE id=%s", (id,))
    db.commit()

    return redirect('/admin_dashboard')
#================== RUN ==================
if __name__ == '__main__':
    app.run(debug=True)