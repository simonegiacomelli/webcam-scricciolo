let intervals = [];
let day_template = document.querySelector('#day_template');
let group_template = document.querySelector('#group_template');
let days_div = document.getElementById('days_div')
let img_div = document.getElementById('img_div')
let img_tag = document.getElementById('img_tag')
let progress_tag = document.getElementById('progress_tag')
let automatic_tag = document.getElementById('automatic_tag')
let automatic_msec = document.getElementById('automatic_msec')
let mask_images = document.getElementById('mask_images')
let selected_group = {}
let image_list = [];
let image_index = 0;


async function get(url) {
    let response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    } else {
        return await response.json();
    }
}

async function delete_click() {
    if (!confirm('Are you sure?'))
        return;
    let result = await get('/api/delete_group?filename=' + image_list[0]);
    await metadata_refresh()
}

function img_click() {
    reset_index()
}

function reset_index() {
    image_index = 0;
    load_image();
    automatic_next();
}

function index_description() {
    return `${selected_group[0]} (${image_index + 1}/${image_list.length})`;
}

function load_image() {
    progress_tag.value = Math.round((image_index + 1) / image_list.length * 100)
    filename = image_list[image_index]
    console.log(`loading ${filename}`)
    img_div.innerHTML = index_description() + '<br>' + filename
    img_tag.src = '/api/image?filename=' + filename
}

function change_image(offset) {
    let index = image_index + offset;
    if (index < 0 || index >= image_list.length) {
        img_div.innerHTML = index_description() + '<br>no further images';
        return false;
    }
    image_index = index;
    load_image();
    return true;
}

function clearAllIntervals() {
    while (intervals.length > 0) clearInterval(intervals.pop())
}

function getInterval() {
    return parseInt(automatic_msec.value, 10);
}

function automatic_next() {
    clearAllIntervals();
    if (!automatic_tag.checked)
        return;
    let msec = getInterval();
    intervals.push(setInterval(() => {
        if (msec !== getInterval())
            automatic_next();
        else if (!automatic_tag.checked || !change_image(1))
            clearAllIntervals();
    }, msec));
}

function automatic_next_click() {
    if (automatic_tag.checked)
        automatic_next();
    else
        clearAllIntervals();
}

async function group_click(day, group) {
    selected_group = group
    let filename = group[1];
    let gs = await get('/api/group_summary?filename=' + filename);
    // let img = document.createElement('img')
    image_list = (mask_images.checked) ? gs : gs.filter(e => !e.endsWith('m.jpg'));
    image_index = 0;
    load_image()
    automatic_next();
}

function append_day(day) {
    let day_instance = day_template.content.cloneNode(true);
    let temp_day = (day_instance.querySelectorAll('#temp_day'))[0];
    let temp_groups_container = day_instance.querySelector('#temp_groups_container');
    day_id = day[0]
    groups = day[1]
    temp_day.id = `day-${day_id}`
    temp_day.innerHTML = day_id;

    temp_groups_container.id = `group-container-${day_id}`

    days_div.appendChild(day_instance);

    for (let group of groups) {
        // debugger;
        let group_instance = group_template.content.cloneNode(true);
        let temp_group = group_instance.querySelector('#temp_group')
        temp_group.id = `group-${group[0]}`
        temp_group.innerHTML = group[0]
        temp_group.href = '#'
        temp_groups_container.appendChild(group_instance);
        temp_group.onclick = (event) => {
            group_click(day, group)
        }
    }

}

async function load_metadata() {
    console.log('load_metadata()');
    let summary = await get('/api/summary');
    days_div.innerHTML = '';
    for (let day of summary) {
        append_day(day)
    }
}

async function metadata_refresh() {
    let result = await get('/api/metadata_refresh');
    console.log(result)
    await load_metadata()
}

progress_tag.addEventListener('click', function (e) {
    let value_clicked = e.offsetX * this.max / this.offsetWidth / 100;
    console.log(value_clicked)
    image_index = Math.ceil(image_list.length * value_clicked) - 1
    load_image()
});
