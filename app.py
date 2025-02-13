from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
from supabase import create_client
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

app = Flask(__name__)


from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)


@app.route('/')
def nest():
    recent_blogs = supabase.table('stream').select('title', 'content').order('created_at', desc=True).limit(3).execute()
    recent_poems = supabase.table('verse').select('title', 'poem').order('created_at', desc=True).limit(3).execute()
    
    recent_items = []
    if recent_blogs.data:
        for blog in recent_blogs.data:
            recent_items.append({
                "title": blog['title'],
                "description": blog['content'][:100] + "...",  # Truncate content for preview
                "link": url_for('stream') 
            })
    if recent_poems.data:
        for poem in recent_poems.data:
            recent_items.append({
                "title": poem['title'],
                "description": poem['poem'][:100] + "...",  # Truncate poem for preview
                "link": url_for('verse')  
            })

    return render_template('nest.html', recent_items=recent_items)
  

@app.route('/stream', methods=['GET', 'POST'])
def stream():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Insert blog post into Supabase
        try:
            data = supabase.table('stream').insert({
                'title': title,
                'content': content,
                'author_id': None # Add author_id when authentication is implemented
            }).execute()
            return redirect(url_for('stream'))
        except Exception as e:
            return str(e), 500
    
    # Fetch all blog posts
    blogs = supabase.table('stream').select('*').order('created_at', desc=True).execute()
    return render_template('stream.html', blogs=blogs.data)

@app.route('/verse')
def verse():
    return render_template('verse.html')  
@app.route('/stash')
def stash():
    return render_template('stash.html') 
@app.route('/muse')
def muse():
    return render_template('muse.html')  
@app.route('/haven')
def haven():
    return render_template('haven.html') 
@app.route('/origin')
@app.route('/origin', methods=['GET', 'POST'])
def origin():
    return render_template('origin.html')

@app.route('/scout')
def scout():
    return render_template('scout.html') 
if __name__ == '__main__':
    app.run(debug=True)
