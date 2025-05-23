particlesJS('particles-js', {
    particles: {
        number: {
            value: 300, // number of particles
            density: {
                enable: true,
                value_area: 800
            }
        },
        color: {
            value: "#00e6e6" // bright cyan particle color
        },
        shape: {
            type: "circle",
            stroke: {
                width: 0,
                color: "#000000"
            }
        },
        opacity: {
            value: 0.5, // lower opacity for dots
            random: true,
            anim: {
                enable: false
            }
        },
        size: {
            value: 2, // smaller dot size
            random: true,
            anim: {
                enable: true,
                speed: 3,
                size_min: 0.3
            }
        },
        line_linked: {
            enable: true,
            distance: 100, // distance between dots
            color: "#00e6e6", // bright connecting lines
            opacity: 0.2, // dim but visible lines
            width: 1
        },
        move: {
            enable: true,
            speed: 2, // faster movement
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

document.addEventListener("DOMContentLoaded", function () {
    // find the container with data
    const dataContainer = document.getElementById("data-container");

    // extract data from attributes
    const movementStats = JSON.parse(dataContainer.dataset.movementStats);
    const peakHourData = JSON.parse(dataContainer.dataset.peakHour);

    // now you can use the data to build charts
    console.log(movementStats);
    console.log(peakHourData);

    // example usage with Chart.js
    const ctx = document.getElementById("myChart").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: Object.keys(movementStats),
            datasets: [{
                label: "Movement Statistics",
                data: Object.values(movementStats),
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1,
            }]
        },
    });
});

document.getElementById("file-input").addEventListener("change", function(event) {
    const fileName = event.target.files[0].name;
    document.getElementById("file-name").innerText = fileName;
});
