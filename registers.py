import datetime
import prodigy

from collections import namedtuple
from prodigy.components.loaders import JSONL


Register = namedtuple('Register', 'id text subregisters')


REGISTER_HIERARCHY = [
    Register('MT', 'Machine translated or generated', []),
    Register('LY', 'Lyrical (e.g. song, poem)', []),
    Register('SP-main', 'Spoken (e.g. transcribed speech, TV/movie script)', [
        Register('SP-it', 'Interview', []),
        Register('SP', 'Other spoken (e.g. formal speech, audio transcript)', []),
    ]),
    Register('ID', 'Interactive discussion (e.g. discussion/QA forum)', []),
    Register('NA-main', 'Narrative / report on events (e.g. news, sports)', [
        Register('NA-ne', 'News report', []),
        Register('NA-sr', 'Sports report', []),
        Register('NA-nb', 'Narrative blog (e.g. travel, lifestyle, or personal blog)', []),
        Register('NA', 'Other narrative (e.g. fiction, magazine article)', []),
    ]),
    Register('IP-main', 'Informational persuasion (e.g. editorial, persuasive essay)', [
        Register('IP-ds', 'Description with intent to sell', []),
        Register('IP-ed', 'Editorial / news+opinion blog', []),
        Register('IP', 'Other informational persuasion (e.g. persuasive essay)', []),
    ]),
    Register('IN-main', 'Informational description (e.g. encyclopedia or research article, FAQ)', [
        Register('IN-en', 'Encyclopedia article', []),
        Register('IN-ra', 'Research article', []),
        Register('IN-dtp', 'Description of a thing or person (excluding encyclopedia articles)', []),
        Register('IN-fi', 'FAQ', []),
        Register('IN-lt', 'Legal terms and conditions', []),
        Register('IN', 'Other informational description (e.g. course material, blog for informing the reader)', []),
    ]),
    Register('HI-main', 'How-to / instruction (e.g. recipe)', [
        Register('HI-re', 'Recipe', []),
        Register('HI', 'Other how-to (objective step-by-step instructions on how to do something)', []),
    ]),
    Register('OP-main', 'Opinion (e.g. review, advice)', [
        Register('OP-rv', 'Review', []),
        Register('OP-ob', 'Opinion blog', []),
        Register('OP-rs', 'Denominational religious blog / sermon', []),
        Register('OP-av', 'Advice', []),
        Register('OP', 'Other opinion (any other opinionated text)', []),
    ]),
]

MAIN_REGISTER_IDS = [m.id for m in REGISTER_HIERARCHY]

SUBREGISTER_IDS = [s.id for m in REGISTER_HIERARCHY for s in m.subregisters]

SUBREGISTER_IDS_BY_MAIN_ID = {
    m.id: [s.id for s in m.subregisters] for m in REGISTER_HIERARCHY
}

JAVASCRIPT = f"""
const MAIN_REGISTER_IDS = {MAIN_REGISTER_IDS}
const SUBREGISTER_IDS = {SUBREGISTER_IDS}
const SUBREGISTER_IDS_BY_MAIN_ID = {SUBREGISTER_IDS_BY_MAIN_ID}
""" """

function hideAllSubregisters() {
  var subregisterDivs = document.getElementsByClassName('subregister')
  for (let e of subregisterDivs) {
    e.style.display = 'none'
  }
}

document.addEventListener('prodigyanswer', event => {
  hideAllSubregisters()
})

function wrapInDiv(element) {
  var div = document.createElement('div')
  element.parentNode.insertBefore(div, element)
  div.appendChild(element)
  return div
}

function tweakOptionDisplay(id, isMainRegister, hasSubRegister) {
  var checkbox = document.getElementById(id)
  var div = checkbox.parentElement
  // Hide keyboard shortcut divs
  var kbShortcut = checkbox.nextSibling.nextSibling
  if (kbShortcut !== null) {
    kbShortcut.style.display = 'none'
  }
  // Add 'main-register', 'subregister' and 'has-subregister' classes for CSS
  div = wrapInDiv(div)    // prodigy resets classes
  if (isMainRegister) {
    div.classList.add('main-register')
  } else {
    div.classList.add('subregister')
  }
  if (hasSubRegister) {
    div.classList.add('has-subregister')
  }
}

function updateSubregisters(id, mainSelected) {
  var subregisterIds = SUBREGISTER_IDS_BY_MAIN_ID[id]
  console.log(subregisterIds)
}

function addCheckboxListener(id) {
  var checkbox = document.getElementById(id)
  checkbox.addEventListener('click', event => {
    console.log('Change', event)
    updateSubregisters(id, checkbox.checked)
  })
}

function getDivByRegisterId(id) {
  return document.getElementById(id).parentNode.parentNode
}

// Add a top-level event listener to adjust subregister element state
// when main register element status changes. It would be cleaner to
// have this as a 'change' event listener on the relevant checkboxes,
// but prodigy changes the 'checked' status programmatically in cases,
// and this doesn't trigger the 'change' event.
window.addEventListener('click', event => {
  //console.log('Window-click', event)
  //console.log('MT state:', document.getElementById('MT').checked)
  for (let mainId of MAIN_REGISTER_IDS) {
    var checkbox = document.getElementById(mainId)
    for (let subId of  SUBREGISTER_IDS_BY_MAIN_ID[mainId]) {
      var div = getDivByRegisterId(subId)
      display = checkbox.checked ? 'block' : 'none'
      div.style.display = display
    }
  }
})

document.addEventListener('prodigymount', event => {
  console.log('Mount: ', event)
  for (let id of MAIN_REGISTER_IDS) {
    subregisterIds = SUBREGISTER_IDS_BY_MAIN_ID[id]
    tweakOptionDisplay(id, true, !!subregisterIds.length)
    addCheckboxListener(id)
  }
  for (let id of SUBREGISTER_IDS) {
    tweakOptionDisplay(id, false, false)
  }
})
"""

def iso8601_now():
    """Return current time in ISO 8601 format w/o microseconds."""
    return datetime.datetime.now().replace(microsecond=0).isoformat(' ')


def count_lines(file_path):
    return sum(1 for i in open(file_path))


@prodigy.recipe(
    'registers',
    dataset=('The dataset to save to', 'positional', None, str),
    file_path=('Path to texts', 'positional', None, str),
    annotator=('Annotator name', 'positional', None, str),
)
def registers(dataset, file_path, annotator):
    """Annotate the sentiment of texts using different mood options."""
    stream = JSONL(file_path)     # load in the JSONL file
    # stream = add_options(stream)  # add options to each task

    # TODO need to remove previously annotated
    total_lines = count_lines(file_path)
    def progress(controller, update_return_value):
        return controller.total_annotated / total_lines

    def add_label(stream):
        for task in stream:
            task['label'] = task.get('doc_title')
            yield task
    stream = add_label(stream)
    stream = add_options(stream)

    def before_db(examples):
        for e in examples:
            if 'created' not in e:
                e['created'] = iso8601_now()
            if 'annotator' not in e:
                e['annotator'] = annotator
        return examples

    return {
        'dataset': dataset,
        'stream': stream,
        'view_id': 'choice',
        'progress': progress,
        'before_db': before_db,
        'config': {
            'javascript': JAVASCRIPT,
        },
    }


def add_options(stream):
    flat_registers = []
    for m in REGISTER_HIERARCHY:
        flat_registers.append(m)
        for s in m.subregisters:
            flat_registers.append(s)

    options = [
        { 'id': r.id, 'text': r.text } for r in flat_registers
    ]
    for task in stream:
        task['options'] = options
        yield task
