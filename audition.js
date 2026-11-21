(() => {
  const canvas = document.querySelector("#wave");
  const audio = document.querySelector(".scope audio");
  if (!canvas || !audio) return;
  const context = canvas.getContext("2d");
  if (!context) return;
  let samples = [];
  function draw() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    if (!width || !height) return;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const middle = height / 2;
    context.lineWidth = 1;
    context.strokeStyle = "#3b5557";
    context.beginPath();
    for (let i = 0; i <= 4; i++) {
      let x = Math.round(i * width / 4) + .5;
      context.moveTo(x, 0); context.lineTo(x, height);
    }
    for (let i = 1; i <= 3; i++) {
      const y = Math.round(height * i / 4) + .5;
      context.moveTo(0, y); context.lineTo(width, y);
    }
    context.stroke();
    const palette = ["#a8bbc0", "#f2ab6d", "#9adcc3", "#69c9d3"];
    const step = width / samples.length;
    samples.forEach((value, i) => {
      const amp = Math.max(.65, value * (middle-4));
      context.fillStyle = palette[Math.min(3, Math.floor(4*i/samples.length))];
      context.fillRect(i*step, middle-amp, Math.max(.8,step*.82), amp*2);
    });
    if (audio.currentTime > 0 && !audio.ended) {
      context.fillStyle = "#fff";
      context.fillRect(Math.min(width-2,width*audio.currentTime/8),0,2,height);
    }
  }
  fetch("media/envelope.json").then(r => r.json()).then(data => {
    samples = data;
    draw();
  }).catch(() => { canvas.hidden = true; });
  new ResizeObserver(draw).observe(canvas);
  audio.addEventListener("timeupdate", draw);
  audio.addEventListener("ended",draw);
})();
