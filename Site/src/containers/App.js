import React, { Component } from 'react';
import { Switch, Route } from 'react-router-dom'

import Home from './Home.js'
import User from './User.js'

export default class App extends Component {
  render() {
    return (
      <div className="page-container">
        <div className="container">
          <Switch>
            <Route exact path='/' component={Home}/>
            <Route path='/user/:username'component={User}/> // props.match.params
          </Switch>
        </div>
      </div>
    )
  }
}
