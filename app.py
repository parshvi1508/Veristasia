from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
from supabase import create_client
from flask_wtf.csrf import CSRFProtect

from groq import Groq
from flask_socketio import SocketIO
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

app = Flask(__name__)
socketio = SocketIO(app)
groq_client = Groq(api_key=os.getenv("YOUR_GROQ_API_KEY"))


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)





@socketio.on('send_message')
def handle_message(data):
    user_message = data['message']
    
    # Call Groq API
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are Muse, a helpful chatbot."},
            {"role": "user", "content": user_message}
        ],
        model="mixtral-8x7b-32768"
    )
    
    bot_response = response.choices[0].message.content
    socketio.emit('receive_message', {'message': bot_response})
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
  
@app.route('/stream')
def stream():
    blogs = supabase.table('stream').select('*').eq('status', 'published').order('created_at', desc=True).execute()
    return render_template('stream.html', blogs=blogs.data)

@app.route('/verse')
def verse():
    verses = supabase.table('verse').select('*').eq('status', 'published').order('created_at', desc=True).execute()
    return render_template('verse.html', verses=verses.data)

@app.route('/stash')
def stash():
    stashes = supabase.table('stash').select('*').eq('status', 'published').order('created_at', desc=True).execute()
    return render_template('stash.html', stashes=stashes.data)

@app.route('/muse')
def muse():
    return render_template('muse.html')

@app.route('/haven', methods=['GET', 'POST'])
def haven():
    if request.method == 'POST':
        content_type = request.form.get('content_type')
        title = request.form.get('title')
        content = request.form.get('content')
        status = request.form.get('status', 'draft')  # Default to draft if not specified

        try:
            data = {
                'title': title,
                'status': status
            }
            
            if content_type == 'stream':
                data['content'] = content
                table_name = 'stream'
            elif content_type == 'verse':
                data['poem'] = content  # Note: Verse table uses 'poem' instead of 'content'
                table_name = 'verse'
            elif content_type == 'stash':
                data['notes'] = content  # Note: Stash table uses 'notes' instead of 'content'
                data['resource_name'] = title
                data['category'] = request.form.get('category', '')  # Add category for stash
                table_name = 'stash'
            else:
                return "Invalid content type", 400

            supabase.table(table_name).insert(data).execute()
            
            # Update Haven table with new counts
            if status == 'draft':
                supabase.table('haven').update({'draft_count': supabase.raw('draft_count + 1')}).execute()
            else:
                supabase.table('haven').update({'post_count': supabase.raw('post_count + 1')}).execute()
                
            return redirect(url_for('haven'))
        except Exception as e:
            return str(e), 500

    # Fetch drafts and published content
    drafts_stream = supabase.table('stream').select('*').eq('status', 'draft').order('created_at', desc=True).execute()
    drafts_verse = supabase.table('verse').select('*').eq('status', 'draft').order('created_at', desc=True).execute()
    drafts_stash = supabase.table('stash').select('*').eq('status', 'draft').order('created_at', desc=True).execute()
    
    published_stream = supabase.table('stream').select('*').eq('status', 'published').order('created_at', desc=True).execute()
    published_verse = supabase.table('verse').select('*').eq('status', 'published').order('created_at', desc=True).execute()
    published_stash = supabase.table('stash').select('*').eq('status', 'published').order('created_at', desc=True).execute()

    return render_template('haven.html', 
                         drafts_stream=drafts_stream.data,
                         drafts_verse=drafts_verse.data,
                         drafts_stash=drafts_stash.data,
                         published_stream=published_stream.data,
                         published_verse=published_verse.data,
                         published_stash=published_stash.data)

@app.route('/scout', methods=['GET'])
def scout():
    query = request.args.get('query', '')
    content_type = request.args.get('content_type', 'all')

    try:
        # Log the search query
        supabase.table('scout').insert({
            'search_query': query,
            'results': None  #can store results count or relevant info here
        }).execute()

        if content_type in ['stream', 'verse', 'stash']:
            if content_type == 'stash':
                results = (supabase.table(content_type)
                          .select('*')
                          .eq('status', 'published')
                          .ilike('resource_name', f'%{query}%')
                          .execute()
                          .data)
            else:
                results = (supabase.table(content_type)
                          .select('*')
                          .eq('status', 'published')
                          .ilike('title', f'%{query}%')
                          .execute()
                          .data)
        else:
            # Search across all content types
            stream_results = (supabase.table('stream')
                            .select('*')
                            .eq('status', 'published')
                            .ilike('title', f'%{query}%')
                            .execute()
                            .data)
            verse_results = (supabase.table('verse')
                           .select('*')
                           .eq('status', 'published')
                           .ilike('title', f'%{query}%')
                           .execute()
                           .data)
            stash_results = (supabase.table('stash')
                           .select('*')
                           .eq('status', 'published')
                           .ilike('resource_name', f'%{query}%')
                           .execute()
                           .data)
            
            # Add content type to each result
            for result in stream_results:
                result['content_type'] = 'stream'
            for result in verse_results:
                result['content_type'] = 'verse'
            for result in stash_results:
                result['content_type'] = 'stash'
                
            results = stream_results + verse_results + stash_results

        return render_template('scout.html', results=results, query=query, content_type=content_type)
    
    except Exception as e:
        return f"Search error: {str(e)}", 500
     
     
@app.route('/origin')
def origin():
    return render_template('origin.html')
if __name__ == '__main__':
    app.run(debug=True)
