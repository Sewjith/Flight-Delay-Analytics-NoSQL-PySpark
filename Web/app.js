const data = window.SITE_DATA;

const formatInt = new Intl.NumberFormat("en-US");
const formatDecimal = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const formatCompact = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2,
});

let activeSection = "All";

/* ── Intersection Observer for scroll animations ── */
const scrollObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        // Stagger child animations
        const children = entry.target.querySelectorAll(
          ".metric-card, .card, .chart-card, .mini-metric, .leader-card"
        );
        children.forEach((child, i) => {
          child.style.animationDelay = `${i * 0.08}s`;
          child.style.animation = `countUp 0.5s ease-out ${i * 0.08}s both`;
        });
      }
    });
  },
  { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
);

/* ── Active nav tracking ── */
const navObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        document.querySelectorAll(".nav-links a").forEach((a) => {
          a.style.background =
            a.getAttribute("href") === `#${id}`
              ? "rgba(99, 102, 241, 0.12)"
              : "";
          a.style.color =
            a.getAttribute("href") === `#${id}` ? "#818cf8" : "";
        });
      }
    });
  },
  { threshold: 0.3 }
);

function formatValue(value) {
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return formatInt.format(value);
    }
    return formatDecimal.format(value);
  }
  return value ?? "—";
}

function tableMarkup(rows) {
  if (!rows.length) {
    return '<tbody><tr><td>No rows extracted.</td></tr></tbody>';
  }

  const columns = Object.keys(rows[0]);
  return `
    <thead><tr>${columns
      .map(
        (column) =>
          `<th>${column.replaceAll("_", " ")}</th>`
      )
      .join("")}</tr></thead>
    <tbody>${rows
      .map(
        (row) =>
          `<tr>${columns
            .map(
              (column) =>
                `<td>${formatValue(row[column])}</td>`
            )
            .join("")}</tr>`
      )
      .join("")}</tbody>
  `;
}

function renderTable(tableEl, rows) {
  tableEl.innerHTML = tableMarkup(rows);
}

/* ── Metric icons mapping ── */
const metricIcons = {
  "Flights processed": "✈️",
  "Cancellation rate": "🚫",
  "Delay rate": "⏱️",
  "Average distance": "📏",
  "Years covered": "📅",
  "Total flights": "🛫",
  "Cancelled flights": "❌",
  "Avg arrival delay": "⏳",
};

function getExecutiveSummary() {
  const overall = { ...(data.highlights?.overallSummary || {}) };
  const yearly = data.highlights?.yearlySummary || [];

  if (
    (overall.cancellation_rate === undefined ||
      overall.cancellation_rate === null) &&
    overall.total_flights &&
    overall.total_cancelled_flights !== undefined
  ) {
    overall.cancellation_rate =
      (overall.total_cancelled_flights / overall.total_flights) * 100;
  }

  if (
    (overall.delay_rate === undefined || overall.delay_rate === null) &&
    yearly.length
  ) {
    let weightedDelay = 0;
    let totalFlights = 0;

    yearly.forEach((row) => {
      if (
        typeof row.total_flights === "number" &&
        typeof row.delay_rate === "number"
      ) {
        weightedDelay += row.total_flights * row.delay_rate;
        totalFlights += row.total_flights;
      }
    });

    if (totalFlights > 0) {
      overall.delay_rate = weightedDelay / totalFlights;
    }
  }

  return overall;
}

function renderHero() {
  document.getElementById("hero-subtitle").textContent =
    data.project.subtitle;
  document.getElementById("stack-list").innerHTML = data.project.stack
    .map((item) => `<span class="stack-pill">${item}</span>`)
    .join("");

  const overall = getExecutiveSummary();
  const heroMetrics = [
    {
      label: "Years covered",
      value: data.project.years.join(" · "),
    },
    {
      label: "Total flights",
      value: formatCompact.format(overall.total_flights || 0),
    },
    {
      label: "Cancelled flights",
      value: formatCompact.format(overall.total_cancelled_flights || 0),
    },
    {
      label: "Avg arrival delay",
      value: `${formatDecimal.format(overall.avg_arrival_delay || 0)} min`,
    },
  ];

  document.getElementById("hero-metrics").innerHTML = heroMetrics
    .map(
      (metric) => `
      <div class="mini-metric">
        <div class="mini-label">${metricIcons[metric.label] || "📊"} ${metric.label}</div>
        <div class="mini-value">${metric.value}</div>
      </div>
    `
    )
    .join("");
}

function renderSummary() {
  const overall = getExecutiveSummary();
  const cards = [
    {
      label: "Flights processed",
      value: formatInt.format(overall.total_flights || 0),
      caption: "Combined 2016-2018 analysis set",
    },
    {
      label: "Cancellation rate",
      value: `${formatDecimal.format(overall.cancellation_rate || 0)}%`,
      caption: "Share of flights marked cancelled",
    },
    {
      label: "Delay rate",
      value: `${formatDecimal.format(overall.delay_rate || 0)}%`,
      caption: "Flights with arrival delay above 15 minutes",
    },
    {
      label: "Average distance",
      value: `${formatDecimal.format(overall.avg_distance || 0)} mi`,
      caption: "Mean route distance in the combined set",
    },
  ];

  document.getElementById("overall-cards").innerHTML = cards
    .map(
      (card) => `
      <article class="metric-card">
        <div class="metric-label">${metricIcons[card.label] || "📊"} ${card.label}</div>
        <div class="metric-value">${card.value}</div>
        <div class="metric-caption">${card.caption}</div>
      </article>
    `
    )
    .join("");

  renderTable(
    document.getElementById("yearly-table"),
    data.highlights.yearlySummary
  );

  const outcomes = [
    ...data.highlights.flightStatus.map((row) => ({
      label: row.flight_status,
      value: formatCompact.format(row.flight_count),
      meta: "status split",
    })),
    ...data.highlights.delayCategories.map((row) => ({
      label: row.delay_category,
      value: formatCompact.format(row.flight_count),
      meta: "delay category",
    })),
  ];

  document.getElementById("outcome-breakdown").innerHTML = outcomes
    .map(
      (item) => `
      <div class="leader-card">
        <div class="stat-label">${item.label}</div>
        <div class="stat-value">${item.value}</div>
        <div class="stat-meta">${item.meta}</div>
      </div>
    `
    )
    .join("");
}

function renderCharts() {
  document.getElementById("chart-gallery").innerHTML = data.charts
    .map(
      (chart) => `
      <article class="card chart-card">
        <img src="${chart.image}" alt="${chart.title}" loading="lazy">
        <div class="chart-copy">
          <div class="chart-meta">${chart.section}</div>
          <h3>${chart.title}</h3>
          <p>${chart.description}</p>
        </div>
      </article>
    `
    )
    .join("");
}

function renderMl() {
  const balance = data.ml.balance;
  const balanceItems = [
    {
      label: "Original delayed",
      value: formatInt.format(balance.originalDelayed || 0),
    },
    {
      label: "Original on-time",
      value: formatInt.format(balance.originalOnTime || 0),
    },
    {
      label: "Balanced delayed",
      value: formatInt.format(balance.balancedDelayed || 0),
    },
    {
      label: "Balanced on-time",
      value: formatInt.format(balance.balancedOnTime || 0),
    },
  ];

  document.getElementById("balance-cards").innerHTML = balanceItems
    .map(
      (item) => `
      <div class="mini-metric">
        <div class="mini-label">${item.label}</div>
        <div class="mini-value">${item.value}</div>
      </div>
    `
    )
    .join("");

  const bestDt =
    [...data.ml.decisionTree.trials].sort((a, b) => b.auc - a.auc)[0] || {};
  const bestRf = data.ml.randomForest.best;
  const gbt = data.ml.gradientBoostedTree;

  const medalIcons = ["🥇", "🥈", "🥉"];
  const leaderboard = [
    {
      label: "Gradient Boosted Tree",
      value: `AUC ${formatDecimal.format(gbt.auc || 0)}`,
      meta: `Accuracy ${formatDecimal.format(gbt.accuracy || 0)} · Precision ${formatDecimal.format(gbt.precision || 0)} · Recall ${formatDecimal.format(gbt.recall || 0)}`,
    },
    {
      label: "Random Forest",
      value: `AUC ${formatDecimal.format(bestRf.auc || 0)}`,
      meta: `Accuracy ${formatDecimal.format(bestRf.accuracy || 0)} · maxDepth ${bestRf.maxDepth || "—"} · minInstances ${bestRf.minInstancesPerNode || "—"}`,
    },
    {
      label: "Decision Tree",
      value: `AUC ${formatDecimal.format(bestDt.auc || 0)}`,
      meta: `Accuracy ${formatDecimal.format(bestDt.accuracy || 0)} · maxDepth ${bestDt.maxDepth || "—"} · minInstances ${bestDt.minInstances || "—"}`,
    },
  ];

  document.getElementById("model-leaderboard").innerHTML = leaderboard
    .map(
      (item, i) => `
      <div class="leader-card">
        <div class="leader-label">${medalIcons[i]} ${item.label}</div>
        <div class="leader-value">${item.value}</div>
        <div class="leader-meta">${item.meta}</div>
      </div>
    `
    )
    .join("");

  renderTable(
    document.getElementById("dt-table"),
    data.ml.decisionTree.trials
  );

  const maxImportance = Math.max(
    ...data.ml.featureImportances.map((item) => item.importance),
    0.0001
  );
  document.getElementById("feature-bars").innerHTML = data.ml.featureImportances
    .sort((a, b) => b.importance - a.importance)
    .map(
      (item) => `
      <div class="feature-row">
        <div class="feature-head">
          <strong>${item.feature}</strong>
          <span>${formatDecimal.format(item.importance)}</span>
        </div>
        <div class="feature-track">
          <div class="feature-fill" style="width: ${(item.importance / maxImportance) * 100}%"></div>
        </div>
      </div>
    `
    )
    .join("");
}

function renderFeaturedTables() {
  const featuredIds = new Set(data.meta.featuredTableIds);
  const featuredTables = data.tables.filter((table) =>
    featuredIds.has(table.id)
  );

  document.getElementById("featured-tables").innerHTML = featuredTables
    .map(
      (table) => `
      <article class="card">
        <div class="card-header">
          <h3>${table.title}</h3>
          <p>${table.section}${table.datasetName ? ` · ${table.datasetName}` : ""}</p>
        </div>
        ${table.note ? `<p class="explorer-note">${table.note}</p>` : ""}
        <div class="table-scroll">
          <table>${tableMarkup(table.rows.slice(0, 8))}</table>
        </div>
      </article>
    `
    )
    .join("");
}

function renderOutputFilters() {
  const container = document.getElementById("section-filters");
  const sections = [
    "All",
    ...data.meta.sectionOrder.filter((section) =>
      data.tables.some((table) => table.section === section)
    ),
  ];
  container.innerHTML = sections
    .map(
      (section) => `
      <button class="chip ${section === activeSection ? "is-active" : ""}" data-section="${section}" type="button">
        ${section}
      </button>
    `
    )
    .join("");

  container.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      activeSection = chip.dataset.section;
      renderOutputFilters();
      renderOutputExplorer();
    });
  });
}

function renderOutputExplorer() {
  const query = document
    .getElementById("output-search")
    .value.trim()
    .toLowerCase();
  const list = data.tables.filter((table) => {
    const searchable = [
      table.title,
      table.section,
      table.datasetName || "",
      table.note || "",
    ]
      .join(" ")
      .toLowerCase();
    const matchesQuery = !query || searchable.includes(query);
    const matchesSection =
      activeSection === "All" || table.section === activeSection;
    return matchesQuery && matchesSection;
  });

  document.getElementById(
    "output-count"
  ).textContent = `${list.length} table outputs shown`;

  const container = document.getElementById("output-list");
  if (!list.length) {
    container.innerHTML =
      '<div class="muted-empty">No outputs match the current filter.</div>';
    return;
  }

  container.innerHTML = list
    .map(
      (table) => `
      <details class="explorer-item">
        <summary class="explorer-summary">
          <div class="explorer-topline">
            <h3>${table.title}</h3>
            <div class="explorer-meta">${table.section} · ${table.displayedRowCount} rows${table.datasetName ? ` · ${table.datasetName}` : ""}</div>
          </div>
        </summary>
        ${table.note ? `<div class="explorer-note">${table.note}</div>` : ""}
        <div class="table-scroll">
          <table>${tableMarkup(table.rows)}</table>
        </div>
      </details>
    `
    )
    .join("");
}

function initScrollAnimations() {
  document.querySelectorAll(".animate-on-scroll").forEach((el) => {
    scrollObserver.observe(el);
  });

  document.querySelectorAll("section[id]").forEach((section) => {
    navObserver.observe(section);
  });
}

function bootstrap() {
  renderHero();
  renderSummary();
  renderCharts();
  renderMl();
  renderFeaturedTables();
  renderOutputFilters();
  renderOutputExplorer();

  document
    .getElementById("output-search")
    .addEventListener("input", renderOutputExplorer);

  // Initialize scroll animations
  requestAnimationFrame(() => {
    initScrollAnimations();
  });
}

bootstrap();
