from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Todo {self.id}: {self.title}>'


@app.route('/')
def index():
    filter_by = request.args.get('filter', 'all')

    if filter_by == 'active':
        todos = Todo.query.filter_by(completed=False).order_by(Todo.created_at.desc()).all()
    elif filter_by == 'completed':
        todos = Todo.query.filter_by(completed=True).order_by(Todo.created_at.desc()).all()
    else:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()

    total = Todo.query.count()
    active_count = Todo.query.filter_by(completed=False).count()
    completed_count = Todo.query.filter_by(completed=True).count()

    return render_template(
        'index.html',
        todos=todos,
        filter_by=filter_by,
        total=total,
        active_count=active_count,
        completed_count=completed_count
    )


@app.route('/add', methods=['POST'])
def add_todo():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')

    if not title:
        flash('Title cannot be empty.', 'error')
        return redirect(url_for('index'))

    todo = Todo(title=title, description=description or None, priority=priority)
    db.session.add(todo)
    db.session.commit()
    flash('Task added successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    return redirect(url_for('index', filter=request.args.get('filter', 'all')))


@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')

        if not title:
            flash('Title cannot be empty.', 'error')
            return render_template('edit.html', todo=todo)

        todo.title = title
        todo.description = description or None
        todo.priority = priority
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', todo=todo)


@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    flash('Task deleted.', 'info')
    return redirect(url_for('index', filter=request.args.get('filter', 'all')))


@app.route('/clear-completed', methods=['POST'])
def clear_completed():
    Todo.query.filter_by(completed=True).delete()
    db.session.commit()
    flash('Completed tasks cleared.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
