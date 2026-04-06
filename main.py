from flask import Flask,render_template,request
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/home_page')
def home_page():
    return render_template('home_page.html')

@app.route('/tbr')
def tbr():
    return render_template('tbr.html')

@app.route('/to_watch')
def to_watch():
    return render_template('to_watch.html')

@app.route('/read')
def read():
    return render_template('read.html')

@app.route('/watched')
def watched():
    return render_template('watched.html')

file_data = {
    'tbr': ('tbr_books.json', 'tbr','TBR'),
    'to_watch': ('to_watch.json', 'to_watch','To Watch'),
    'read': ('read_books.json', 'read','Read'),
    'watched': ('watched.json', 'watched','Watched'),
}

# list page
@app.route('/list_page/<list_name>')
def list_page(list_name):
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',show_list=False, show_delete=False)
    file_name, key_name, display_name = file_data[list_name]
    
    with open(file_name) as f:
        data = json.load(f)

    sorted_list = sorted(data[key_name], key=lambda x: x['title'])
    return render_template('status.html',tbr_books=sorted_list,list_name=display_name,list_key=key_name, show_list=True, show_delete=False)

# taking user input from search box for all lists
@app.route('/handle-action/<list_name>', methods=['POST'])
def add_and_search_item(list_name):
    action = request.form.get('action')
    title = (request.form.get('title') or '').title()
    author = (request.form.get('author') or '').title()

    file_name, key_name, display_name = file_data[list_name]
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',show_list=False, show_delete=False)

    #opening json file to read and write data
    with open(file_name) as f:
        data = json.load(f)

    # selecting action to perform based on user input
    ## add item to list
    if action == 'add':
        new_item = {
            'title': title,
            'author': author,
        }

        if new_item not in data[key_name] and title != '':
            data[key_name].append(new_item)

        with open(file_name, 'w') as f:
            json.dump(data, f)

        return render_template(f'{list_name}.html')
    
    ## search for item in list
    elif action == 'search':
        matches = []
        for item in data[key_name]:
            if title in item['title'].title():
                if author:
                    if item['author'].title() == author:
                        matches.append(item)
                else:
                    matches.append(item)

        if matches:
            return render_template('status.html', list_key=key_name, list_name=display_name, matches=matches, message='Item(s) found in list.', show_delete=True, show_list=False)
        elif title == '':
            return render_template('status.html', list_key=key_name, message='Please enter a title to search.', show_list=False, show_delete=False)
        else:
            return render_template('status.html', list_key=key_name, message='Item not found. Try adding it to the list first.', show_list=False, show_delete=False)
        
# delete item from list
@app.route('/delete/<list_name>', methods=['POST'])
def delete_item(list_name):
    title = (request.form.get('title') or '').title()
    author = (request.form.get('author') or '').title()

    file_name, key_name, display_name = file_data[list_name]
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',show_list=False, show_delete=False)

    with open(file_name) as f:
        data = json.load(f)

    found = False
    for item in data[key_name]:
        if item['title'] == title and item['author'] == author:
            data[key_name].remove(item)
            found = True
            break

    if found:
        with open(file_name, 'w') as f:
            json.dump(data, f)
        return render_template('status.html', message='Deleted successfully', list_name=list_name, list_key=key_name, show_list=False, show_delete=False)
    else:
        return render_template('status.html', message='Item not found. Try adding it to the list first.', list_name=list_name, list_key=key_name, show_list=False, show_delete=False)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)