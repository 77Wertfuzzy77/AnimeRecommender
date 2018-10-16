import React, { Component } from 'react';

export default class Header extends Component {
  render() {
    return (
      <div>
        <div>
          <div className="absolute" id="main-image"></div>
          <div className="absolute" id="legs"></div>
        </div>
        <div className="title">
          <div className="floater">
            Steins; Guidance
          </div>
        </div>
      </div>
    )
  }
}
