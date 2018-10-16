import React, { Component } from 'react';

export default class User extends Component {
  render () {
    const uid = this.props.match.params.username;

    return (
      <div>{uid}</div>
    )
  }
}
