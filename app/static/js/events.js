document.addEventListener("DOMContentLoaded", function () {
    const events = [
        {
            id: 1,
            name: "Raccolta alimentare – Croce Rossa",
            lat: 41.1171,
            lng: 16.8719,
            description: "Aiuta nella raccolta e distribuzione di beni alimentari ai bisognosi nel quartiere Libertà.",
            url: "/event/1"
        },
        {
            id: 2,
            name: "Pulizia del parco Rossani",
            lat: 41.1188,
            lng: 16.8612,
            description: "Unisciti a noi per pulire e riqualificare una delle aree verdi centrali di Bari.",
            url: "/event/2"
        },
        {
            id: 3,
            name: "Supporto anziani – Municipio I",
            lat: 41.1144,
            lng: 16.8753,
            description: "Accompagnamento e supporto pratico per anziani soli nel quartiere Madonnella.",
            url: "/event/3"
        }
    ];

    const map = L.map('map').setView([41.1171, 16.8719], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const list = document.getElementById("event-list");
    const search = document.getElementById("search");

    events.forEach(evt => {
        const popupContent = `
            <strong>${evt.name}</strong><br>
            <small>${evt.description}</small><br>
            <a href="${evt.url}" class="btn btn-sm btn-primary mt-2">Vai all'evento</a>
        `;
        const marker = L.marker([evt.lat, evt.lng]).addTo(map)
            .bindPopup(popupContent);

        const li = document.createElement("li");
        li.className = "list-group-item";
        li.innerHTML = `<strong>${evt.name}</strong><br><small>${evt.description}</small>`;
        li.addEventListener("click", () => {
            map.setView([evt.lat, evt.lng], 15);
            marker.openPopup();
        });
        list.appendChild(li);
    });

    search.addEventListener("input", function () {
        const value = this.value.toLowerCase();
        list.querySelectorAll("li").forEach(li => {
            li.style.display = li.textContent.toLowerCase().includes(value) ? "" : "none";
        });
    });
});

fetch('/api/events')
  .then(res => res.json())
  .then(events => {
    events.forEach(evt => {
      const marker = L.marker([evt.lat, evt.lng]).addTo(map)
        .bindPopup(`<strong>${evt.name}</strong><br>${evt.description}`);
      const li = document.createElement("li");
      li.className = "list-group-item";
      li.textContent = evt.name;
      li.addEventListener("click", () => {
        map.setView([evt.lat, evt.lng], 15);
        marker.openPopup();
      });
      list.appendChild(li);
    });
  });
