from flask import Flask,render_template,request,redirect,url_for
import psycopg2,os

app = Flask(__name__)

# opening database
def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# setting up SQLite database to store user data
def db_setup():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    list_name TEXT NOT NULL,
                    user_name TEXT NOT NULL
                )
                ''')

    connection.commit()
    cursor.close()
    connection.close()

# home page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/home_page')
def home_page():
    user_name = (request.args.get('user_name') or '').title()
    if not user_name:
        return render_template('index.html')
    return render_template('home_page.html', user_name=user_name)

@app.route('/tbr')
def tbr():
    return render_template('tbr.html',user_name=request.args.get('user_name'))

@app.route('/to_watch')
def to_watch():
    return render_template('to_watch.html',user_name=request.args.get('user_name'))

@app.route('/read')
def read():
    return render_template('read.html',user_name=request.args.get('user_name'))

@app.route('/watched')
def watched():
    return render_template('watched.html',user_name=request.args.get('user_name'))

file_data = {
    'tbr': ('tbr','TBR'),
    'to_watch': ('to_watch','To Watch'),
    'read': ('read','Read'),
    'watched': ('watched','Watched'),
}

# list page
@app.route('/list_page/<list_name>')
def list_page(list_name):
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',user_name=request.args.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]
    
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        'SELECT title, author FROM storage where list_name = %s AND user_name = %s', 
        (list_name, request.args.get('user_name'))
    )

    rows = cursor.fetchall()  # list of sqlite3.Row objects (not in dict format)
    cursor.close()
    connection.close()

    # converting list of sqlite3.Row objects to list of dicts
    data = [{'title': row[0], 'author': row[1]} for row in rows]

    # sorting by title
    sorted_list = sorted(data, key=lambda x: x['title'])
    return render_template('status.html',tbr_books=sorted_list, user_name=request.args.get('user_name'), display_name=display_name, key_name=key_name, show_list=True, show_delete=False)

# taking user input from search box for all lists
@app.route('/handle-action/<list_name>', methods=['POST'])
def add_and_search_item(list_name):
    # get title and author from form, convert to title case
    action = request.form.get('action')
    title = (request.form.get('title') or '').title()
    author = (request.form.get('author') or '').title()

    
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',user_name=request.form.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]

    # selecting action to perform based on user input
    ## add item to list
    if action == 'add':
        if title != '':
            connection = get_db()
            cursor = connection.cursor()

            cursor.execute(
                'INSERT INTO storage (title, author, list_name, user_name) VALUES (%s, %s, %s, %s)', 
                (title, author, list_name, request.form.get('user_name'))
            )

            connection.commit()
            cursor.close()
            connection.close()

        return redirect(url_for(list_name, user_name=request.form.get('user_name')))
    
    ## search for item in list
    elif action == 'search':
        connection = get_db()
        cursor = connection.cursor()

        if author:
            cursor.execute(
                'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s',
                (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'))
            )
        else:
            cursor.execute(
                'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND list_name = %s AND user_name = %s',
                (title.lower().strip(), list_name, request.form.get('user_name'))
            )
        
        matches = cursor.fetchall()
        cursor.close()
        connection.close()

        if matches:
            return render_template('status.html', user_name=request.form.get('user_name'), key_name=key_name, display_name=display_name, matches=matches, message='Item(s) found in list.', show_delete=True, show_list=False)
        elif title == '':
            return render_template('status.html', user_name=request.form.get('user_name'), key_name=key_name, message='Please enter a title to search.', show_list=False, show_delete=False)
        else:
            return render_template('status.html', user_name=request.form.get('user_name'), key_name=key_name, message='Item not found. Try adding it to the list first.', show_list=False, show_delete=False)
        
# delete item from list
@app.route('/delete/<list_name>', methods=['POST'])
def delete_item(list_name):
    title = (request.form.get('title') or '').title()
    author = (request.form.get('author') or '').title()

    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',user_name=request.form.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        'DELETE FROM storage WHERE TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s',
        (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'))
    )
    connection.commit()    
    

    if cursor.rowcount > 0 :
        if author:
            message=f'{title} by {author} deleted successfully'
        else:
            message=f'{title} deleted successfully'
    else:
        if author:
            message=f'"{title} by {author}" not found. Try adding it to the list first.'
        else:
            message=f'"{title}" not found. Try adding it to the list first.'

    cursor.close()
    connection.close()

    return render_template('status.html', user_name=request.form.get('user_name'), message=message, display_name=display_name, key_name=key_name, show_list=False, show_delete=False)


if __name__ == '__main__':
    db_setup()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)