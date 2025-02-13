// haven.js
document.addEventListener('DOMContentLoaded', function() {
    initializeEditors();
    setupTodoList();
    setupScreenTimeReminder();
});

function initializeEditors() {
    const editorConfig = {
        height: 500,
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount'
        ],
        toolbar: 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help',
        content_style: 'body { font-family: Inter, sans-serif; }',
        setup: function(editor) {
            editor.on('change', function() {
                autoSaveDraft(editor.getContent());
            });
        }
    };

    window.openEditor = function(type) {
        const modal = document.createElement('div');
        modal.className = 'editor-modal';
        modal.id = 'editor-modal';
        
        const content = `
            <div class="editor-content">
                <h2>${type.charAt(0).toUpperCase() + type.slice(1)} Editor</h2>
                <input type="text" id="content-title" placeholder="Title" class="form-control mb-3">
                <textarea id="content-editor"></textarea>
                <div class="button-group mt-3">
                    <button onclick="saveContent('${type}')" class="btn btn-primary">Publish</button>
                    <button onclick="saveDraft('${type}')" class="btn btn-secondary">Save Draft</button>
                    <button onclick="closeEditor()" class="btn btn-danger">Close</button>
                </div>
            </div>
        `;
        
        modal.innerHTML = content;
        document.body.appendChild(modal);
        
        const customConfig = {...editorConfig};
        if (type === 'verse') {
            customConfig.content_style = 'body { font-family: Georgia, serif; }';
        }
        
        tinymce.init({
            ...customConfig,
            selector: '#content-editor'
        });
    };
}

async function saveContent(type) {
    const title = document.getElementById('content-title').value;
    const content = tinymce.activeEditor.getContent();
    
    try {
        const response = await fetch(`/${type}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content })
        });
        
        if (response.ok) {
            closeEditor();
            location.reload();
        }
    } catch (error) {
        console.error('Error saving content:', error);
    }
}

function setupTodoList() {
    const todoList = {
        items: JSON.parse(localStorage.getItem('todos') || '[]'),
        
        add: function(task) {
            this.items.push({
                id: Date.now(),
                task,
                completed: false
            });
            this.save();
            this.render();
        },
        
        toggle: function(id) {
            const todo = this.items.find(item => item.id === id);
            if (todo) {
                todo.completed = !todo.completed;
                this.save();
                this.render();
            }
        },
        
        delete: function(id) {
            this.items = this.items.filter(item => item.id !== id);
            this.save();
            this.render();
        },
        
        save: function() {
            localStorage.setItem('todos', JSON.stringify(this.items));
        },
        
        render: function() {
            const list = document.getElementById('todo-items');
            list.innerHTML = this.items.map(todo => `
                <li>
                    <input type="checkbox" ${todo.completed ? 'checked' : ''} 
                           onchange="todoList.toggle(${todo.id})">
                    <span style="${todo.completed ? 'text-decoration: line-through' : ''}">${todo.task}</span>
                    <button onclick="todoList.delete(${todo.id})" class="btn btn-sm btn-danger">Delete</button>
                </li>
            `).join('');
        }
    };
    
    window.todoList = todoList;
    todoList.render();
}

function setupScreenTimeReminder() {
    let reminderShown = false;
    
    setInterval(() => {
        if (!reminderShown) {
            const reminder = document.getElementById('screen-time-reminder');
            reminder.style.display = 'block';
            reminderShown = true;
            
            setTimeout(() => {
                reminder.style.display = 'none';
                reminderShown = false;
            }, 30000); // Hide after 30 seconds
        }
    }, 7200000); // Check every 2 hours
}

function closeEditor() {
    const modal = document.getElementById('editor-modal');
    if (modal) {
        tinymce.activeEditor.destroy();
        modal.remove();
    }
}

// Auto-save drafts every 30 seconds
let autoSaveTimeout;
function autoSaveDraft(content) {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        const title = document.getElementById('content-title').value;
        localStorage.setItem('draft_' + Date.now(), JSON.stringify({
            title,
            content,
            timestamp: new Date().toISOString()
        }));
    }, 30000);
}