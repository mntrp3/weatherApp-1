var chart = dc.compositeChart("#test");
d3.csv("static/morley3.csv", function(error, experiments) {

  experiments.forEach(function(x) {
    x.Speed = +x.Speed;
  });

  var ndx                 = crossfilter(experiments),
      scatterDimension    = ndx.dimension(function(d) { return [+d.Run, d.Speed * d.Run / 1000]; }),
      scatterGroup        = scatterDimension.group(),
      lineDimension       = ndx.dimension(function(d) { return +d.Run; }),
      lineGroup           = lineDimension.group().reduceSum(function (d) {
          return d.Speed * d.Run / 4000;
      });

    chart
        .width(768)
        .height(480)
        .x(d3.scale.linear().domain([6,20]))
        .yAxisLabel("This is the Y Axis!")
        .dimension(scatterDimension)
        .legend(dc.legend().x(70).y(10).itemHeight(13).gap(5))
        .compose([
            dc.scatterPlot(chart)
                .group(scatterGroup, "Blue Group")
                .colors("blue"),
            dc.scatterPlot(chart)
                .group(scatterGroup, "Red Group")
                .colors("red")
                .valueAccessor(function (d) { return d.key[1] + 5; }),
            dc.lineChart(chart)
                .dimension(lineDimension)
                .group(lineGroup, "Line Group")
        ]);

  chart.render();
});