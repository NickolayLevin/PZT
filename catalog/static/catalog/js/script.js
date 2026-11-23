const searchInput = document.querySelector(".releases-toolbar__search input");

const genreFilter = document.querySelector("#genre-filter");

const yearFilter = document.querySelector("#year-filter");

const releaseCards = document.querySelectorAll(".release-card");

const emptyMessage = document.querySelector(".releases-empty");

const typeFilter = document.querySelector("#type-filter");

const sortFilter = document.querySelector(
  ".releases-toolbar__filters select:last-child",
);

// Releases filtering and sorting

if (
  searchInput &&
  genreFilter &&
  yearFilter &&
  typeFilter &&
  sortFilter &&
  emptyMessage
) {
  function filterReleases() {
    const searchValue = searchInput.value.trim().toLowerCase();

    const selectedGenre = genreFilter.value;
    const selectedYear = yearFilter.value;
    const selectedType = typeFilter.value;

    let visibleCards = 0;

    releaseCards.forEach(function (card) {
      const title = card
        .querySelector(".release-card__title")
        .textContent.toLowerCase();

      const artist = card
        .querySelector(".release-card__artist")
        .textContent.toLowerCase();

      const genres = (card.dataset.genre || "").split(" ");
      const year = card.dataset.year;
      const type = card.dataset.type;
      const matchesSearch =
        title.includes(searchValue) || artist.includes(searchValue);

      const matchesGenre =
        selectedGenre === "" || genres.includes(selectedGenre);

      const matchesYear = selectedYear === "" || year === selectedYear;

      const matchesType = selectedType === "" || type === selectedType;

      const isVisible =
        matchesSearch && matchesGenre && matchesYear && matchesType;
      card.hidden = !isVisible;

      if (isVisible) {
        visibleCards++;
      }
    });

    // Sorting

    const releaseGrid = document.querySelector(".release-grid");

    const sortedCards = Array.from(releaseCards);

    if (sortFilter.value === "newest") {
      sortedCards.sort((a, b) => b.dataset.date.localeCompare(a.dataset.date));
    }

    if (sortFilter.value === "oldest") {
      sortedCards.sort((a, b) => a.dataset.date.localeCompare(b.dataset.date));
    }

    if (sortFilter.value === "title") {
      sortedCards.sort((a, b) => {
        const titleA = a.querySelector(".release-card__title").textContent;

        const titleB = b.querySelector(".release-card__title").textContent;

        return titleA.localeCompare(titleB);
      });
    }

    if (sortFilter.value === "rating") {
      sortedCards.sort(
        (a, b) => Number(b.dataset.rating || 0) - Number(a.dataset.rating || 0),
      );
    }

    sortedCards.forEach((card) => {
      releaseGrid.appendChild(card);
    });

    emptyMessage.hidden = visibleCards > 0;
  }

  searchInput.addEventListener("input", filterReleases);
  genreFilter.addEventListener("change", filterReleases);
  yearFilter.addEventListener("change", filterReleases);
  sortFilter.addEventListener("change", filterReleases);
  typeFilter.addEventListener("change", filterReleases);
}

// Artists search

const artistSearch = document.querySelector("#artist-search");

if (artistSearch) {
  const artistCards = document.querySelectorAll(".artist-card");
  const artistsEmpty = document.querySelector(".artists-empty");

  artistSearch.addEventListener("input", function () {
    const searchValue = artistSearch.value.trim().toLowerCase();

    let visibleArtists = 0;

    artistCards.forEach(function (card) {
      const artistName = card
        .querySelector(".artist-card__name")
        .textContent.toLowerCase();

      const isVisible = artistName.includes(searchValue);

      card.hidden = !isVisible;

      if (isVisible) {
        visibleArtists++;
      }
    });

    if (artistsEmpty) {
      artistsEmpty.hidden = visibleArtists > 0;
    }
  });
}
