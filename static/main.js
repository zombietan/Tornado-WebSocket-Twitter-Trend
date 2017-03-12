window.onload = function() {

  "use strict";

  const makeTable = (data) => {
    let tr = $('<tr/>');
    $('<th/>').text(data.rank).appendTo(tr);
    let a = $('<a/>').attr("href", data.url).text(data.name);
    $('<td/>').append(a).appendTo(tr);
    $('<td/>').text(data.volume).appendTo(tr);
    return tr;
  };

  class Count3min {
    constructor() {
      this.count = 180;
    }

    decrement() {
      let limit = setInterval(() => {
        this.count--;
        let text;
        if (this.count > 120) {
          text = '3分後に更新';
        } else if (this.count > 60) {
          text = '2分後に更新';
        } else if (this.count > 10) {
          text = '1分後に更新';
        } else {
          text = this.count;
        }
        document.getElementById("timestamp").innerHTML = text;
        if (this.count == 0) {
          clearInterval(limit);
        }
      }, 1000);
    }
  }

  class Trend {
    constructor(eventData) {
      this.trendArray = JSON.parse(eventData);
      this.count = 0;
    }

    appendTrend() {
      let timer = setInterval(() => {
        let data = this.trendArray[this.count];
        let tr = makeTable(data);
        if(this.count < 25) {
          tr.appendTo('#left').addClass('magictime swashIn');
        } else {
          tr.appendTo('#right').addClass('magictime swashIn');
        }
        this.count++;
        if(this.count == this.trendArray.length) {
          clearInterval(timer);
        }
      }, 50);
    }
  }

  if (window["WebSocket"]) {
    const conn = new ReconnectingWebSocket(location.protocol.replace("http", "ws") + "//" + location.host + "/ws");

    conn.onmessage = function(event) {
      $('tbody').empty();
      let timeLimit = new Count3min().decrement();
      let trend = new Trend(event.data).appendTrend();
    };
  }

};
