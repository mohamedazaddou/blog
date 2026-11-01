// Filtres + pagination côté client (aucun serveur, aucun build).
const PAGE = 24;
const grid = document.getElementById('grid');
const cards = Array.from(grid.children);
const q = document.getElementById('q');
const empty = document.getElementById('empty');
const loadmore = document.getElementById('loadmore');
const sourceChips = document.querySelectorAll('#sources .chip');
const topicChips = document.querySelectorAll('#topics .chip');

let activeSource = '';
let activeTag = '';
let activeLang = '';
let shown = 0;
let visible = [];

function matches(card) {
  if (activeSource && card.dataset.src !== activeSource) return false;
  if (activeLang && card.dataset.lang !== activeLang) return false;
  if (activeTag) {
    const tags = (card.dataset.tags || '').split(',');
    if (!tags.includes(activeTag)) return false;
  }
  const term = q.value.trim().toLowerCase();
  if (term) {
    const hay = (card.dataset.search || '') + ' ' + card.dataset.src.toLowerCase();
    if (!term.split(/\s+/).every(t => hay.includes(t))) return false;
  }
  return true;
}

function apply() {
  visible = cards.filter(matches);
  cards.forEach(c => { c.hidden = true; });
  visible.slice(0, PAGE).forEach(c => { c.hidden = false; });
  shown = Math.min(PAGE, visible.length);
  empty.hidden = visible.length > 0;
  loadmore.hidden = visible.length <= shown;
}

loadmore.addEventListener('click', () => {
  visible.slice(shown, shown + PAGE).forEach(c => { c.hidden = false; });
  shown = Math.min(shown + PAGE, visible.length);
  loadmore.hidden = visible.length <= shown;
});

sourceChips.forEach(chip => chip.addEventListener('click', () => {
  const v = chip.dataset.src;
  activeSource = activeSource === v ? '' : v;
  sourceChips.forEach(c => c.classList.toggle('is-active', c.dataset.src === activeSource));
  if (!activeSource) sourceChips[0].classList.add('is-active');
  apply();
  window.scrollTo({ top: document.querySelector('.toolbar').offsetTop, behavior: 'smooth' });
}));

topicChips.forEach(chip => chip.addEventListener('click', () => {
  const v = chip.dataset.tag;
  activeTag = activeTag === v ? '' : v;
  topicChips.forEach(c => c.classList.toggle('is-active', c.dataset.tag === activeTag));
  apply();
}));

const langChips = document.querySelectorAll('#langs .chip');
langChips.forEach(chip => chip.addEventListener('click', () => {
  activeLang = chip.dataset.lang;
  langChips.forEach(c => c.classList.toggle('is-active', c.dataset.lang === activeLang));
  apply();
}));

q.addEventListener('input', () => { apply(); });

document.getElementById('reset').addEventListener('click', () => {
  q.value = '';  activeSource = ''; activeTag = ''; activeLang = '';
  sourceChips.forEach(c => c.classList.toggle('is-active', c.dataset.src === ''));
  topicChips.forEach(c => c.classList.remove('is-active'));
  langChips.forEach(c => c.classList.toggle('is-active', c.dataset.lang === ''));
  apply();
});

apply();
