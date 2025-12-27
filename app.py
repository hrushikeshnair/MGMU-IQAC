from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import secrets
import json
import os

app = Flask(__name__)
# NOTE: keep a secure secret in production (env var or config)
app.secret_key = 'dev-secret-change-me'

# JSON-based data storage
def load_institutes():
    try:
        with open('institutes.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_institutes():
    with open('institutes.json', 'w') as f:
        json.dump(app.config['INSTITUTES'], f)

def load_faculty_details():
    try:
        with open('faculty_details.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # store as a list of faculty entries
        return []

def save_faculty_details():
    with open('faculty_details.json', 'w') as f:
        json.dump(app.config['FACULTY_DETAILS'], f)

def load_faculty_reports():
    try:
        with open('faculty_reports.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_faculty_reports():
    with open('faculty_reports.json', 'w') as f:
        json.dump(app.config['FACULTY_REPORTS'], f)

def load_grades():
    try:
        with open('grades.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_grades():
    with open('grades.json', 'w') as f:
        json.dump(app.config['GRADES'], f)

def load_credits_data():
    try:
        with open('credits.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_research_papers():
    try:
        with open('research_papers.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_research_papers():
    with open('research_papers.json', 'w') as f:
        json.dump(app.config['RESEARCH_PAPERS'], f)

def load_conference_papers():
    try:
        with open('conference_papers.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_conference_papers():
    with open('conference_papers.json', 'w') as f:
        json.dump(app.config['CONFERENCE_PAPERS'], f)

def load_book_publications():
    try:
        with open('book_publications.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_book_publications():
    with open('book_publications.json', 'w') as f:
        json.dump(app.config['BOOK_PUBLICATIONS'], f)

def load_book_chapters():
    try:
        with open('book_chapters.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_book_chapters():
    with open('book_chapters.json', 'w') as f:
        json.dump(app.config['BOOK_CHAPTERS'], f)

# load at startup
app.config['INSTITUTES'] = load_institutes()
app.config['FACULTY_DETAILS'] = load_faculty_details()
app.config['FACULTY_REPORTS'] = load_faculty_reports()
app.config['GRADES'] = load_grades()
app.config['CREDITS'] = load_credits_data()
app.config['RESEARCH_PAPERS'] = load_research_papers()
app.config['CONFERENCE_PAPERS'] = load_conference_papers()
app.config['BOOK_PUBLICATIONS'] = load_book_publications()
app.config['BOOK_CHAPTERS'] = load_book_chapters()


# Default credentials for roles (development only - replace with secure store)
CREDENTIALS = {
    'auditor': '1234',
    'university_iqac_coordination': 'adminpass',
    'registrar': 'registrarpass',
    'vice_chancellor': 'vcpass',
    'director': 'directorpass',
    'iqac_coordinators': 'iqacpass',
    'hod': 'hodpass',
    'faculty': 'facultypass',
}

ROLE_DISPLAY = {
    'auditor': 'Auditor',
    'university_iqac_coordination': 'University IQAC Coordination',
    'registrar': 'Registrar',
    'vice_chancellor': 'Vice Chancellor',
    'director': 'Director',
    'iqac_coordinators': 'IQAC Coordinators',
    'hod': 'HOD',
    'faculty': 'Faculty',
}

# Roles that must approve a faculty report for it to be considered fully approved
REQUIRED_APPROVERS = [
    'auditor',
    'university_iqac_coordination',
    'registrar',
    'vice_chancellor',
    'director',
    'iqac_coordinators',
    'hod'
]

@app.context_processor
def inject_now():
    return {
        'current_year': datetime.now().year,
        'is_admin': session.get('is_admin', False),
        'role': session.get('role', None),
        'selected_institute': session.get('selected_institute', None),
        'institutes': app.config['INSTITUTES'],
        'ROLE_DISPLAY': ROLE_DISPLAY
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    # Generate a fresh captcha on GET
    if request.method == "GET":
        session['captcha'] = ''.join(secrets.choice('0123456789') for _ in range(5))

    if request.method == "POST":
        login_by = request.form.get("login_by")
        password = request.form.get("password")
        captcha = request.form.get("captcha")
        expected = session.get('captcha')

        # Verify credentials for any configured role
        expected_password = CREDENTIALS.get(login_by)
        if expected_password and password == expected_password and captcha == expected:
            # Admin gets special privileges
            if login_by in ['university_iqac_coordination', 'registrar']:
                session['is_admin'] = True
                session['selected_institute'] = None
                session.pop('captcha', None)
                return redirect(url_for('admin'))

            # Non-admin roles
            session.pop('is_admin', None)
            session['selected_institute'] = None
            session['role'] = login_by
            message = f"Login Successful ({ROLE_DISPLAY.get(login_by, login_by)})"
            session.pop('captcha', None)
            return redirect(url_for('dashboard'))

        message = "Invalid Credentials"
        # rotate captcha after a failed attempt
        session['captcha'] = ''.join(secrets.choice('0123456789') for _ in range(5))
    # Ensure a captcha exists before rendering
    if 'captcha' not in session:
        session['captcha'] = ''.join(secrets.choice('0123456789') for _ in range(5))

    return render_template("login.html", message=message)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Only allow access to admins
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('institute_name', '').strip()
        if name:
            # avoid duplicates
            if name not in app.config['INSTITUTES']:
                app.config['INSTITUTES'].append(name)
                save_institutes()
    return render_template('admin.html', institutes=app.config['INSTITUTES'])


@app.route('/dashboard')
def dashboard():
    # Allow access to any logged-in role or admin
    if not (session.get('is_admin') or session.get('role')):
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session.get('role'), institutes=app.config['INSTITUTES'])

@app.route('/faculty_details', methods=['GET', 'POST'])
def faculty_details():
    allowed_roles = ['faculty', 'iqac_coordinators', 'director', 'university_iqac_coordination', 'registrar']
    if session.get('role') not in allowed_roles and not session.get('is_admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if session.get('role') == 'faculty':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip()
            entry = {
                'name': name,
                'email': email,
                'phone': phone,
                'department': department,
                'created_at': datetime.now().isoformat()
            }
            # append new faculty entry
            if not isinstance(app.config.get('FACULTY_DETAILS'), list):
                app.config['FACULTY_DETAILS'] = []
            app.config['FACULTY_DETAILS'].append(entry)
            save_faculty_details()
            # redirect to avoid form resubmission and show saved values
            return redirect(url_for('faculty_details'))
    # choose the most recent entry to prefill the form for the faculty user
    details = {}
    if isinstance(app.config.get('FACULTY_DETAILS'), list) and app.config['FACULTY_DETAILS']:
        details = app.config['FACULTY_DETAILS'][-1]
    return render_template('faculty_details.html', details=details, all_details=app.config.get('FACULTY_DETAILS', []))

@app.route('/faculty_reports', methods=['GET', 'POST'])
def faculty_reports():
    # Allow creation by faculty and approvals by approver roles
    allowed_roles = ['faculty'] + REQUIRED_APPROVERS
    if session.get('role') not in allowed_roles and not session.get('is_admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        role = session.get('role')
        # Faculty can create reports
        if role == 'faculty':
            report_title = request.form.get('report_title', '').strip()
            report_content = request.form.get('report_content', '').strip()
            if report_title and report_content:
                report = {
                    'title': report_title,
                    'content': report_content,
                    'date': datetime.now().isoformat(),
                    'status': 'pending',
                    'auditor_notes': '',
                    'approvals': {}  # track approvals per role
                }
                app.config['FACULTY_REPORTS'].append(report)
                save_faculty_reports()
        # Approver roles can approve/reject
        elif role in REQUIRED_APPROVERS:
            try:
                report_index = int(request.form.get('report_index', '-1'))
            except ValueError:
                report_index = -1
            action = request.form.get('action')
            approver_notes = request.form.get('approver_notes', '').strip()
            if 0 <= report_index < len(app.config['FACULTY_REPORTS']):
                report = app.config['FACULTY_REPORTS'][report_index]
                if 'approvals' not in report:
                    report['approvals'] = {}
                if action == 'approve':
                    report['approvals'][role] = {'decision': 'approved', 'notes': approver_notes, 'time': datetime.now().isoformat()}
                elif action == 'reject':
                    report['approvals'][role] = {'decision': 'rejected', 'notes': approver_notes, 'time': datetime.now().isoformat()}
                # recompute overall status
                decisions = [v['decision'] for v in report.get('approvals', {}).values()]
                if 'rejected' in decisions:
                    report['status'] = 'rejected'
                else:
                    # check if all required approvers have approved
                    if all(r in report.get('approvals', {}) and report['approvals'][r]['decision'] == 'approved' for r in REQUIRED_APPROVERS):
                        report['status'] = 'approved'
                    else:
                        report['status'] = 'pending'
                save_faculty_reports()
    return render_template('faculty_reports.html', reports=app.config['FACULTY_REPORTS'], required_approvers=REQUIRED_APPROVERS)

@app.route('/audit_reports', methods=['GET', 'POST'])
def audit_reports():
    if session.get('role') != 'auditor':
        return redirect(url_for('login'))
    if request.method == 'POST':
        report_index = int(request.form.get('report_index'))
        status = request.form.get('status')
        notes = request.form.get('auditor_notes', '').strip()
        if 0 <= report_index < len(app.config['FACULTY_REPORTS']):
            report = app.config['FACULTY_REPORTS'][report_index]
            report['auditor_notes'] = notes
            # Record auditor's approval/rejection as part of approvals
            if 'approvals' not in report:
                report['approvals'] = {}
            if status == 'approved':
                report['approvals']['auditor'] = {'decision': 'approved', 'notes': notes, 'time': datetime.now().isoformat()}
            elif status == 'rejected':
                report['approvals']['auditor'] = {'decision': 'rejected', 'notes': notes, 'time': datetime.now().isoformat()}

            # recompute overall status similar to faculty_reports
            decisions = [v['decision'] for v in report.get('approvals', {}).values()]
            if 'rejected' in decisions:
                report['status'] = 'rejected'
            else:
                if all(r in report.get('approvals', {}) and report['approvals'][r]['decision'] == 'approved' for r in REQUIRED_APPROVERS):
                    report['status'] = 'approved'
                else:
                    report['status'] = 'pending'

            save_faculty_reports()
    return render_template('audit_reports.html', reports=app.config['FACULTY_REPORTS'], required_approvers=REQUIRED_APPROVERS)


@app.route('/audit_questionnaire/<int:report_index>', methods=['GET', 'POST'])
def audit_questionnaire(report_index):
    # Only auditors may perform detailed audits
    if session.get('role') != 'auditor':
        return redirect(url_for('login'))

    # basic bounds check
    if report_index < 0 or report_index >= len(app.config['FACULTY_REPORTS']):
        return redirect(url_for('audit_reports'))

    # base questionnaire - extend or move to a config/file if needed
    questions = [
        "Are teaching-learning processes satisfactory?",
        "Is documentation complete and up-to-date?",
        "Are learning outcomes assessed regularly?",
        "Is faculty development activity documented?",
        "Is student feedback handled appropriately?"
    ]

    report = app.config['FACULTY_REPORTS'][report_index]

    # If previous answers contained custom questions, include them in the questions list
    if report.get('audit_answers'):
        for qkey in report['audit_answers'].keys():
            if qkey not in questions:
                questions.append(qkey)

    if request.method == 'POST':
        # Support dynamic number of questions. Client will send total_questions and optional custom_qtext_{i}
        total = int(request.form.get('total_questions', len(questions)))
        # Append any newly created custom questions
        for i in range(len(questions), total):
            qtext = request.form.get(f'custom_qtext_{i}', '').strip()
            if qtext:
                questions.append(qtext)

        answers = {}
        for i, q in enumerate(questions):
            val = request.form.get(f'q_{i}', '').upper()
            if val not in ['Y', 'N']:
                val = 'N'
            answers[q] = val

        notes = request.form.get('auditor_notes', '').strip()
        grade = request.form.get('grade', '').strip()
        institute = request.form.get('institute', '').strip()

        report['audit_answers'] = answers
        report['auditor_notes'] = notes
        report['audit_grade'] = grade
        report['audited_institute'] = institute
        save_faculty_reports()

        # if auditor selected an institute and grade, update grades
        if institute and grade:
            app.config['GRADES'][institute] = grade
            save_grades()

        return redirect(url_for('audit_reports'))

    return render_template('audit_questionnaire.html', report=report, report_index=report_index, questions=questions, institutes=app.config['INSTITUTES'], grades=app.config['GRADES'])

@app.route('/assign_grades', methods=['GET', 'POST'])
def assign_grades():
    if session.get('role') != 'auditor':
        return redirect(url_for('login'))
    if request.method == 'POST':
        institute = request.form.get('institute')
        grade = request.form.get('grade')
        if institute and grade:
            app.config['GRADES'][institute] = grade
            save_grades()
    return render_template('assign_grades.html', institutes=app.config['INSTITUTES'], grades=app.config['GRADES'])

@app.route('/select_institute', methods=['POST'])
def select_institute():
    # Allow admins and other logged-in roles to select a current institute
    if not (session.get('is_admin') or session.get('role')):
        return redirect(url_for('login'))
    inst = request.form.get('institute')
    if inst:
        session['selected_institute'] = inst
    # Send back to the page that submitted the form or to dashboard
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/remove_institute', methods=['POST'])
def remove_institute():
    # only admins may remove
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    inst = request.form.get('institute')
    if inst and inst in app.config['INSTITUTES']:
        try:
            app.config['INSTITUTES'].remove(inst)
            save_institutes()
        except ValueError:
            pass
        if session.get('selected_institute') == inst:
            session['selected_institute'] = None
    return redirect(request.referrer or url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/credits')
def credits():
    return render_template('credits.html', credits=app.config['CREDITS'])

@app.route('/submit_research_paper', methods=['POST'])
def submit_research_paper():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    title = request.form.get('title')
    authors = request.form.get('authors')
    author_position = request.form.get('author_position')
    journal_name = request.form.get('journal_name')
    year = request.form.get('year')
    volume = request.form.get('volume')
    pages = request.form.get('pages')
    isbn_issn = request.form.get('isbn_issn')
    ugc_approved = request.form.get('ugc_approved')
    journal_type = request.form.get('journal_type')
    impact_factor = request.form.get('impact_factor')
    indexing = request.form.get('indexing')
    reviewed = request.form.get('reviewed')
    link = request.form.get('link')
    entry = {
        'title': title,
        'authors': authors,
        'author_position': author_position,
        'journal_name': journal_name,
        'year': year,
        'volume': volume,
        'pages': pages,
        'isbn_issn': isbn_issn,
        'ugc_approved': ugc_approved,
        'journal_type': journal_type,
        'impact_factor': impact_factor,
        'indexing': indexing,
        'reviewed': reviewed,
        'link': link,
        'submitted_at': datetime.now().isoformat()
    }
    if not isinstance(app.config.get('RESEARCH_PAPERS'), list):
        app.config['RESEARCH_PAPERS'] = []
    app.config['RESEARCH_PAPERS'].append(entry)
    save_research_papers()
    return redirect(url_for('dashboard'))

@app.route('/submit_conference_paper', methods=['POST'])
def submit_conference_paper():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    title = request.form.get('title')
    authors = request.form.get('authors')
    author_position = request.form.get('author_position')
    conference_name = request.form.get('conference_name')
    conference_date = request.form.get('conference_date')
    venue = request.form.get('venue')
    proceedings_title = request.form.get('proceedings_title')
    publication_details = request.form.get('publication_details')
    indexing = request.form.get('indexing')
    link = request.form.get('link')
    entry = {
        'title': title,
        'authors': authors,
        'author_position': author_position,
        'conference_name': conference_name,
        'conference_date': conference_date,
        'venue': venue,
        'proceedings_title': proceedings_title,
        'publication_details': publication_details,
        'indexing': indexing,
        'link': link,
        'submitted_at': datetime.now().isoformat()
    }
    if not isinstance(app.config.get('CONFERENCE_PAPERS'), list):
        app.config['CONFERENCE_PAPERS'] = []
    app.config['CONFERENCE_PAPERS'].append(entry)
    save_conference_papers()
    return redirect(url_for('dashboard'))

@app.route('/submit_book_publication', methods=['POST'])
def submit_book_publication():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    faculty_members = request.form.get('faculty_members')
    author_position = request.form.get('author_position')
    book_title = request.form.get('book_title')
    publisher_details = request.form.get('publisher_details')
    publication_type = request.form.get('publication_type')
    isbn = request.form.get('isbn')
    publication_date = request.form.get('publication_date')
    link = request.form.get('link')
    entry = {
        'faculty_members': faculty_members,
        'author_position': author_position,
        'book_title': book_title,
        'publisher_details': publisher_details,
        'publication_type': publication_type,
        'isbn': isbn,
        'publication_date': publication_date,
        'link': link,
        'submitted_at': datetime.now().isoformat()
    }
    if not isinstance(app.config.get('BOOK_PUBLICATIONS'), list):
        app.config['BOOK_PUBLICATIONS'] = []
    app.config['BOOK_PUBLICATIONS'].append(entry)
    save_book_publications()
    return redirect(url_for('dashboard'))

@app.route('/submit_book_chapter', methods=['POST'])
def submit_book_chapter():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))
    faculty_members = request.form.get('faculty_members')
    author_position = request.form.get('author_position')
    book_title = request.form.get('book_title')
    chapter_title = request.form.get('chapter_title')
    publisher_details = request.form.get('publisher_details')
    publication_type = request.form.get('publication_type')
    isbn = request.form.get('isbn')
    publication_date = request.form.get('publication_date')
    link = request.form.get('link')
    entry = {
        'faculty_members': faculty_members,
        'author_position': author_position,
        'book_title': book_title,
        'chapter_title': chapter_title,
        'publisher_details': publisher_details,
        'publication_type': publication_type,
        'isbn': isbn,
        'publication_date': publication_date,
        'link': link,
        'submitted_at': datetime.now().isoformat()
    }
    if not isinstance(app.config.get('BOOK_CHAPTERS'), list):
        app.config['BOOK_CHAPTERS'] = []
    app.config['BOOK_CHAPTERS'].append(entry)
    save_book_chapters()
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
