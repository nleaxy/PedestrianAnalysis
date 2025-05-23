// inicialization for the bg animation
particlesJS('particles-js', {
    particles: {
        number: {
            value: 300,
            density: {
                enable: true,
                value_area: 800
            }
        },
        color: {
            value: "#00e6e6"
        },
        shape: {
            type: "circle",
            stroke: {
                width: 0,
                color: "#000000"
            }
        },
        opacity: {
            value: 0.5,
            random: true,
            anim: {
                enable: false
            }
        },
        size: {
            value: 2,
            random: true,
            anim: {
                enable: true,
                speed: 3,
                size_min: 0.3
            }
        },
        line_linked: {
            enable: true,
            distance: 100,
            color: "#00e6e6",
            opacity: 0.2,
            width: 1
        },
        move: {
            enable: true,
            speed: 2,
            direction: "none",
            random: false,
            straight: false,
            out_mode: "out",
            bounce: false,
            attract: {
                enable: false,
                rotateX: 600,
                rotateY: 1200
            }
        }
    },
    interactivity: {
        detect_on: "canvas",
        events: {
            onhover: {
                enable: true,
                mode: "grab"
            },
            onclick: {
                enable: true,
                mode: "push"
            },
            resize: true
        },
        modes: {
            grab: {
                distance: 200,
                line_linked: {
                    opacity: 0.5
                }
            },
            push: {
                particles_nb: 4
            }
        }
    },
    retina_detect: true
});


// increasing number animation
document.addEventListener("DOMContentLoaded", () => {
    const countElement = document.getElementById("unique-people-count");
    if (countElement) {
        const targetCount = parseInt(countElement.dataset.count, 10);
        let currentCount = 0;
        const duration = 1000;
        const startTime = performance.now();

        const updateCount = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1); // 0 - 1 progress
            currentCount = Math.floor(targetCount * progress);

            countElement.textContent = currentCount;

            if (progress < 1) {
                requestAnimationFrame(updateCount);
            }
        };

        requestAnimationFrame(updateCount);
    }
});


// start of diagram animation
document.addEventListener("DOMContentLoaded", () => {
    const bars = document.querySelectorAll(".bar");
    let maxValue = 0;

    // find max value
    bars.forEach((bar) => {
        const height = parseInt(bar.style.getPropertyValue("--height"), 10) || 0;
        if (height > maxValue) {
            maxValue = height;
        }
    });

    // height of the bars
    bars.forEach((bar) => {
        const height = parseInt(bar.style.getPropertyValue("--height"), 10) || 0;
        bar.style.height = `${230 * (height / maxValue)}px`; // Масштаб высоты столбцов
    });
});

document.getElementById('saveBtn').addEventListener('click', function () {
    const link = document.createElement('a');
    link.href = '/static/results/report.png';
    link.download = 'video-report.png';
    link.click();
});

