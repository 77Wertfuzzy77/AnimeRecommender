import React, { Component } from 'react';

export default class Main extends Component {
  render() {
    return (
      <div>
        <div className="MAL-input-holder holder">
          <input type="text" placeholder="MyAnimeList Username" className="MAL-input" />
        </div>
        <div className="MAL-submit-holder holder">
          <div className="MAL-submit">
            Submit
          </div>
        </div>
      </div>
    )
  }
}
