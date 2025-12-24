const items = window.__AUDIO_ITEMS__ || [];
let currentIndex = 0;

const audio = document.getElementById('audio');
const title = document.getElementById('current-title');
const description = document.getElementById('current-description');
const level = document.getElementById('current-level');
const result = document.getElementById('result');
const answer = document.getElementById('answer');

const selectItem = (index) => {
  if (!items.length) {
    return;
  }
  currentIndex = Math.max(0, Math.min(index, items.length - 1));
  const item = items[currentIndex];
  title.textContent = item.name;
  description.textContent = item.description;
  level.textContent = item.level;
  audio.src = item.audio_url;
  answer.value = '';
  result.textContent = '';

  document.querySelectorAll('.audio-item').forEach((el) => {
    el.classList.toggle('active', Number(el.dataset.id) === item.id);
  });
};

const bindList = () => {
  document.querySelectorAll('.audio-item').forEach((el, index) => {
    el.addEventListener('click', () => selectItem(index));
  });
};

const checkAnswer = async () => {
  const item = items[currentIndex];
  if (!item) {
    return;
  }
  const response = await fetch('/check', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id: item.id, text: answer.value }),
  });
  const data = await response.json();
  if (!data.ok) {
    result.textContent = data.message || '判定に失敗しました。';
    result.className = 'result error';
    return;
  }
  if (data.correct) {
    result.textContent = '正解です！';
    result.className = 'result success';
  } else {
    result.textContent = `不正解：期待「${data.expected_kana} / ${data.expected_kanji}」`;
    result.className = 'result error';
  }
};

if (audio) {
  document.getElementById('prev')?.addEventListener('click', () => selectItem(currentIndex - 1));
  document.getElementById('next')?.addEventListener('click', () => selectItem(currentIndex + 1));
  document.getElementById('pause')?.addEventListener('click', () => audio.pause());
  document.getElementById('stop')?.addEventListener('click', () => {
    audio.pause();
    audio.currentTime = 0;
  });
  document.getElementById('check')?.addEventListener('click', () => checkAnswer());
  document.getElementById('playback-rate')?.addEventListener('change', (event) => {
    audio.playbackRate = Number(event.target.value);
  });
}

bindList();
selectItem(0);
