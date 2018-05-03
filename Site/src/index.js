import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import './assets/css/index.css'
import './assets/css/master.css'



class App extends Component {
  render() {
    return (
      <div className='App'>
        <title>Steins; Guidance</title>
        <link href="https://fonts.googleapis.com/css?family=Neuton" rel="stylesheet" />
        <div className="page-container">
          <div className="container">
            <div className="absolute" id="main-info">
              <div className="mal-text">
                <div className="mal-text-title">
                  Recommendations
                </div>
                <div className="padded-line" />
                <div className="mal-text-content">
                  <p>
                    Info Here <br /> More Info Here <br /> <br /> <br /> And some more
                  </p>
                </div>
              </div>
            </div>
            <div className="absolute" id="main-image" />
            <div className="absolute" id="legs" />
            <div className="title">
              <div className="floater">
                Steins; Guidance
              </div>
            </div>
            <div className="MAL-input-holder holder">
              <input type="text" placeholder="MyAnimeList Username" className="MAL-input" />
            </div>
            <div className="MAL-submit-holder holder">
              <div className="MAL-submit">
                Submit
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('root'));
