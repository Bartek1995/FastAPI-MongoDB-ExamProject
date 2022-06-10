


var options = {
    series: [{
        name: "Ilość",
        data: borrowing_books_values
    }],
    chart: {
    height: 350,
    type: 'line',
    zoom: {
        enabled: false
    }
    },
    dataLabels: {
    enabled: false
    },
    stroke: {
    curve: 'straight'
    },
    title: {
    text: 'Ilość wypożyczeń dla każdego dnia z wybranego okresu',
    align: 'left'
    },
    grid: {
    row: {
        colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
        opacity: 0.5
    },
    },
    xaxis: {
    categories: borrowing_books_days,
    }
    };
  var chart = new ApexCharts(document.querySelector("#chart"), options);
  chart.render();

