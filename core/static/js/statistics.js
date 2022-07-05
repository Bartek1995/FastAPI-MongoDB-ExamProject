


var optionsMainChart = {
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
  var chart = new ApexCharts(document.querySelector("#main-chart"), optionsMainChart);
  chart.render();


var topReadersOptions = {
  series: [{
  name : "Ilość wypożyczonych książek",
  data: top_readers_amount_of_borrowed_books
}],
  chart: {
  height: 350,
  type: 'bar',
  events: {
    click: function(chart, w, e) {
      // console.log(chart, w, e)
    }
  }
},

plotOptions: {
  bar: {
    columnWidth: '45%',
    distributed: true,
  }
},
dataLabels: {
  enabled: true
},
legend: {
  show: false
},
title: {
text: 'Najaktywniejsi czytelnicy',
align: 'left'
},
xaxis: {
  categories: top_readers_reader_name,
  labels: {
    style: {
      fontSize: '12px'
    }
  }
}
};

var chart = new ApexCharts(document.querySelector("#top-readers"), topReadersOptions);
chart.render();



var topBooks = {
  series: [{
  name: 'Ilość wypożyczeń',
  data: top_books_amount
}],
chart: {
  height: 350,
  type: 'bar',
  toolbar: {
        show: true,
        }
},
plotOptions: {
  bar: {
    borderRadius: 10,
    columnWidth: 50,
  }
},
dataLabels: {
  enabled: false
},
stroke: {
  width: 2
},
title: {
text: 'Najpopularniejsze książki',
align: 'left'
},
grid: {
  row: {
    colors: ['#fff', '#f2f2f2']
  }
},
xaxis: {
  labels: {
    rotate: -45,
    minHeight: 80,
    rotateAlways: true,
  },
  categories: top_books_book_titles,
  tickPlacement: 'on'
},
fill: {
  type: 'gradient',
  gradient: {
    shade: 'light',
    type: "horizontal",
    shadeIntensity: 0.25,
    gradientToColors: undefined,
    inverseColors: true,
    opacityFrom: 0.85,
    opacityTo: 0.85,
    stops: [50, 0, 100]
  },
}
};

var chart = new ApexCharts(document.querySelector("#top-books"), topBooks);
chart.render();

var borrowingStatistics = {
  series: borrowing_books_amount_as_percentage,
  chart: {
  width: 380,
  type: 'pie',
},
title: {
text: 'Statystyki wypożyczeń',
align: 'left'
},
legend: {
  position: 'bottom'
},
labels: ['Książki nie oddane', 'Książki oddane'],
responsive: [{
  breakpoint: 480,
  options: {
    chart: {
      width: 200
    },
  }
}]
};

var chart = new ApexCharts(document.querySelector("#borrowing-statistics"), borrowingStatistics);
chart.render();