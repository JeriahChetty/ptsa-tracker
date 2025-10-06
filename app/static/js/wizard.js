document.addEventListener('DOMContentLoaded', function () {
  const form           = document.getElementById('wizard-form');
  const container      = document.getElementById('measures-container');
  const tplMeasure     = document.getElementById('tpl-measure');
  const tplStep        = document.getElementById('tpl-step');
  const deleteToastEl  = document.getElementById('delete-toast');
  const addMeasureBtn  = document.getElementById('add-measure');
  const addExistingBtn = document.getElementById('add-existing-measure');

  if (!container) return;

  // --- Toast / delete confirm (safe globally) ---
  const BS = window.bootstrap || null;
  let toast = null;
  let pendingDelete = null;

  function showDeleteConfirm(doIt) {
    // Use toast if available, otherwise fallback to confirm()
    if (toast) {
      pendingDelete = doIt;
      toast.show();
    } else if (window.confirm('Are you sure you want to delete?')) {
      doIt();
    }
  }

  if (deleteToastEl && BS && BS.Toast) {
    toast = new BS.Toast(deleteToastEl, { animation: true, autohide: false });
    deleteToastEl.addEventListener('hidden.bs.toast', () => { pendingDelete = null; });
    const btnClose = deleteToastEl.querySelector('.btn-close');
    const btnGo    = deleteToastEl.querySelector('.confirm-delete');
    if (btnClose) btnClose.addEventListener('click', () => toast.hide());
    if (btnGo)    btnGo.addEventListener('click', () => { if (pendingDelete) pendingDelete(); toast.hide(); });
  }

  // --- Sortable for measures and steps ---
  if (window.Sortable) {
    Sortable.create(container, {
      animation: 150,
      handle: '.card-title',
      ghostClass: 'dragging',
      onEnd: reindex
    });
  }

  function wireBlock(block) {
    const stepsWrap = block.querySelector('.steps-container');
    if (stepsWrap && window.Sortable && !stepsWrap._sortable) {
      Sortable.create(stepsWrap, {
        animation: 150,
        handle: '.step-number',
        ghostClass: 'dragging',
        onEnd: reindex
      });
      stepsWrap._sortable = true;
    }
  }

  function reindex() {
    container.querySelectorAll('.measure-block').forEach((block, mi) => {
      const titleEl = block.querySelector('.measure-title');
      if (titleEl) titleEl.textContent = `Measure ${mi + 1}`;
      block.dataset.order = String(mi);

      const stepsWrap = block.querySelector('.steps-container');
      if (!stepsWrap) return;

      stepsWrap.querySelectorAll('.step-item').forEach((step, si) => {
        const badge = step.querySelector('.step-number');
        if (badge) badge.textContent = `Step ${si + 1}`;
        step.dataset.order = String(si);
      });
    });
  }

  // Helper used by buildArrayFields
  function addHidden(name, value) {
    if (!form) return;
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value == null ? '' : String(value);
    form.appendChild(input);
  }

  // Collects values from each measure block and emits array fields expected by backend
  function buildArrayFields() {
    container.querySelectorAll('.measure-block').forEach((block) => {
      const v = (sel) => (block.querySelector(sel)?.value || '').trim();

      // NOTE: These selectors match your current markup; adjust if your inputs use classes/data-attrs instead.
      const name         = v('#m-0-name')              || v('.m-name');
      const description  = v('#m-0-measure_detail')    || v('.m-detail');
      const target       = v('#m-0-target')            || v('.m-target');
      const departments  = v('#m-0-departments')       || v('.m-departments');
      const responsible  = v('#m-0-responsible')       || v('.m-responsible');
      const participants = v('#m-0-participants')      || v('.m-participants');
      const urgency      = v('#m-0-urgency')           || v('.m-urgency') || '2';
      const startDate    = v('#m-0-start-date')        || v('.m-start-date'); // informational only (not submitted)
      const endDate      = v('#m-0-end-date')          || v('.m-end-date');   // mapped to timeframe_date

      // Steps: collect titles into newline-separated blob
      const stepsWrap = block.querySelector('.steps-container');
      const stepTitles = [];
      if (stepsWrap) {
        stepsWrap.querySelectorAll('.step-item input[type="text"], .step-item textarea').forEach(inp => {
          const t = (inp.value || '').trim();
          if (t) stepTitles.push(t);
        });
      }
      const stepsBlob = stepTitles.join('\n');

      addHidden('measure_name[]',           name);
      addHidden('measure_description[]',    description);
      addHidden('measure_target[]',         target);
      addHidden('measure_departments[]',    departments);
      addHidden('measure_responsible[]',    responsible);
      addHidden('measure_participants[]',   participants);
      addHidden('measure_urgency[]',        urgency);
      addHidden('measure_duration_days[]',  '');       // keep empty to use start/end approach
      addHidden('measure_timeframe_date[]', endDate);  // map end date to timeframe_date to match backend
      addHidden('measure_steps[]',          stepsBlob);

      // If you later support persisting start_date server-side, also emit:
      // addHidden('measure_start_date[]', startDate);
    });
  }

  // --- Buttons (single definitions, no duplicates) ---
  if (addMeasureBtn && tplMeasure) {
    addMeasureBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const clone = tplMeasure.content.cloneNode(true);
      container.appendChild(clone);
      const last = container.querySelector('.measure-block:last-child');
      if (last) wireBlock(last);
      reindex();
    });
  }

  if (addExistingBtn) {
    addExistingBtn.addEventListener('click', (e) => {
      e.preventDefault();
      alert('Add existing measure: not implemented yet.');
    });
  }

  // Delegated actions (single listener)
  container.addEventListener('click', (e) => {
    // Delete measure
    const measureBtn = e.target.closest('.remove-measure');
    if (measureBtn) {
      const block = measureBtn.closest('.measure-block');
      if (block) showDeleteConfirm(() => { block.remove(); reindex(); });
      return;
    }

    // Add step
    const addStepBtn = e.target.closest('.add-step');
    if (addStepBtn) {
      const block = addStepBtn.closest('.measure-block');
      const steps = block ? block.querySelector('.steps-container') : null;
      if (!block || !steps || !tplStep) return;
      steps.appendChild(tplStep.content.cloneNode(true));
      wireBlock(block);
      reindex();
      return;
    }

    // Delete step
    const stepBtn = e.target.closest('.remove-step');
    if (stepBtn) {
      const step = stepBtn.closest('.step-item');
      if (step) showDeleteConfirm(() => { step.remove(); reindex(); });
      return;
    }
  });

  // On submit: (1) ensure indexes/labels are updated, (2) emit legacy array fields
  if (form) {
    form.addEventListener('submit', () => {
      reindex();
      buildArrayFields();
    });
  }

  // Initial wiring
  container.querySelectorAll('.measure-block').forEach(wireBlock);
  reindex();
});
