const STORAGE_KEY = 'taskflow_tasks';

// --- State: one array of tasks + current filter. Filtered views are derived, never stored. ---
let tasks = load();
let filter = 'all';

const form = document.getElementById('task-form');
const titleInput = document.getElementById('task-title');
const descInput = document.getElementById('task-desc');
const list = document.getElementById('task-list');
const emptyState = document.getElementById('empty-state');
const filterButtons = document.querySelectorAll('#filters button');

const EMPTY_MESSAGES = {
  all: 'No tasks yet. Add one above!',
  active: 'No active tasks.',
  completed: 'No completed tasks yet.'
};

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return []; // corrupted storage -> start fresh instead of crashing
  }
}

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

// --- Mutations: change data, save, render. Every change goes through this one path. ---

function addTask(title, description) {
  tasks.unshift({
    id: crypto.randomUUID(),
    title,
    description,
    completed: false,
    createdAt: Date.now()
  });
  save();
  render();
}

function toggleTask(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  task.completed = !task.completed;
  save();
  render();
}

function deleteTask(id) {
  tasks = tasks.filter(t => t.id !== id);
  save();
  render();
}

function visibleTasks() {
  if (filter === 'active') return tasks.filter(t => !t.completed);
  if (filter === 'completed') return tasks.filter(t => t.completed);
  return tasks;
}

// --- Render: rebuild the list from state. Uses textContent so task text can't inject HTML. ---

function render() {
  const visible = visibleTasks();

  list.innerHTML = '';
  emptyState.hidden = visible.length > 0;
  emptyState.textContent = EMPTY_MESSAGES[filter];

  for (const task of visible) {
    const li = document.createElement('li');
    li.className = 'task' + (task.completed ? ' completed' : '');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = task.completed;
    checkbox.addEventListener('change', () => toggleTask(task.id));

    const text = document.createElement('div');
    text.className = 'task-text';

    const title = document.createElement('span');
    title.className = 'task-title';
    title.textContent = task.title;
    text.appendChild(title);

    if (task.description) {
      const desc = document.createElement('span');
      desc.className = 'task-desc';
      desc.textContent = task.description;
      text.appendChild(desc);
    }

    const del = document.createElement('button');
    del.className = 'delete';
    del.textContent = '×';
    del.setAttribute('aria-label', 'Delete task');
    del.addEventListener('click', () => deleteTask(task.id));

    li.append(checkbox, text, del);
    list.appendChild(li);
  }
}

// --- Events ---

form.addEventListener('submit', e => {
  e.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;
  addTask(title, descInput.value.trim());
  form.reset();
  titleInput.focus();
});

filterButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    filter = btn.dataset.filter;
    filterButtons.forEach(b => b.classList.toggle('active', b === btn));
    render();
  });
});

render(); // initial paint from whatever localStorage has
