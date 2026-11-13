const PAGE_SIZE = 50;
const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
let records = [];
let filtered = [];
let currentPage = 1;

const $ = (id) => document.getElementById(id);

function render() {
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  currentPage = Math.min(currentPage, totalPages);
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageRows = filtered.slice(start, start + PAGE_SIZE);
  $('payroll-body').innerHTML = pageRows.map(row => `
    <tr>
      <td>${row.rank.toLocaleString()}</td>
      <td>${escapeHtml(row.name)}</td>
      <td>${escapeHtml(row.category)}</td>
      <td>${money.format(row.total_pay)}</td>
    </tr>`).join('');
  $('result-count').textContent = `${filtered.length.toLocaleString()} record${filtered.length === 1 ? '' : 's'}`;
  $('page-status').textContent = `Page ${currentPage} of ${totalPages}`;
  $('previous').disabled = currentPage === 1;
  $('next').disabled = currentPage === totalPages;
  renderPages(totalPages);
}

function renderPages(totalPages) {
  const candidates = [...new Set([1, currentPage - 1, currentPage, currentPage + 1, totalPages])]
    .filter(page => page > 0 && page <= totalPages).sort((a, b) => a - b);
  $('pages').innerHTML = candidates.map(page =>
    `<button type="button" data-page="${page}" class="${page === currentPage ? 'active' : ''}" aria-label="Page ${page}">${page}</button>`
  ).join('');
  $('pages').querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
    currentPage = Number(button.dataset.page); render(); document.querySelector('.result-bar').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
}

function applyFilters() {
  const query = $('search').value.trim().toLocaleLowerCase();
  filtered = records.filter(row => row.name.toLocaleLowerCase().includes(query));
  const sort = $('sort').value;
  filtered.sort((a, b) => {
    if (sort === 'pay-asc') return a.total_pay - b.total_pay || a.name.localeCompare(b.name);
    if (sort === 'name-asc') return a.name.localeCompare(b.name);
    if (sort === 'name-desc') return b.name.localeCompare(a.name);
    return b.total_pay - a.total_pay || a.name.localeCompare(b.name);
  });
  currentPage = 1;
  render();
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

async function init() {
  try {
    const response = await fetch('data/payroll.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    records = data.records;
    filtered = [...records];
    const meta = data.metadata;
    $('employee-count').textContent = meta.record_count.toLocaleString();
    $('total-pay').textContent = money.format(meta.source_reported_total);
    $('highest-pay').textContent = money.format(records[0].total_pay);
    $('highest-name').textContent = records[0].name;
    $('average-pay').textContent = money.format(meta.source_reported_total / meta.record_count);
    $('source-link').href = meta.source;
    render();
  } catch (error) {
    $('result-count').textContent = 'Unable to load payroll data.';
    console.error(error);
  }
}

$('search').addEventListener('input', applyFilters);
$('sort').addEventListener('change', applyFilters);
$('previous').addEventListener('click', () => { if (currentPage > 1) { currentPage -= 1; render(); } });
$('next').addEventListener('click', () => { if (currentPage * PAGE_SIZE < filtered.length) { currentPage += 1; render(); } });
init();
