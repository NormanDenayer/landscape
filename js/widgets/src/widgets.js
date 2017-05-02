import React, { Component } from 'react';
import {Panel, ListGroup, ListGroupItem} from 'react-bootstrap';
import './App.css';
import '../node_modules/react-grid-layout/css/styles.css';
import '../node_modules/react-resizable/css/styles.css';
import $ from 'jquery';

import ResponsiveReactGridLayout from 'react-grid-layout';

class Widget extends Component {
  constructor() {
      super();
      this.state = {dirty: false, content: undefined};
      this._loadContent = this._loadContent.bind(this);
  }
  _loadContent() {
      $.ajax({
          url: this.props.data.url,
          method: 'get',
          servercontentType: 'json',
          context: this
      }).done(function(resp) {

      }).fail(function() {

      });
  }
  render() {
      return (<div className="col-md-10">
          <Panel collapsible defaultExpanded style={{overflow_y:scroll, overflow:"hidden"}} header="Panel heading">
              <div className="row"><div className="span4"> <p>item1</p></div></div>
              <div className="row"><div className="span4"> <p>item1</p></div></div>
              <div className="row"><div className="span4"> <p>item1</p></div></div>
              <div className="row"><div className="span4"> <p>item1</p></div></div>
              <div className="row"><div className="span4"> <p>item1</p></div></div>
          </Panel></div>)
  }
}

class Widgets extends Component {
  constructor() {
      super();
      this.state = {widgets: []};
      this.loadGrid = this.loadGrid.bind(this);
  }
  componentDidMount() {
      this.loadGrid()
  }
  loadGrid() {
      $.ajax({
          url: 'http://127.0.0.1:5000/api/v01/user/1/widgets',
          method:'GET',
          servercontentTypee: 'json',
          context: this
      }).done(function(resp){
          console.log(resp);
          this.setState({widgets: resp.widgets})
      }).fail( function(){
          let fakeConfig = {"widgets":[{"h":3,"id":1,"type":1,"url":"/api/v01/user/1/widget/1","w":5,"x":1,"y":0},{"h":3,"id":2,"type":1,"url":"/api/v01/user/1/widget/2","w":5,"x":0,"y":4},{"h":3,"id":3,"type":1,"url":"/api/v01/user/1/widget/3","w":5,"x":0,"y":8},{"h":3,"id":4,"type":1,"url":"/api/v01/user/1/widget/4","w":5,"x":0,"y":12},{"h":3,"id":5,"type":1,"url":"/api/v01/user/1/widget/5","w":5,"x":0,"y":16},{"h":3,"id":6,"type":1,"url":"/api/v01/user/1/widget/6","w":5,"x":0,"y":20}]};
          this.setState({widgets: fakeConfig.widgets})
      });
  }
  createElement(e) {
      return <div key={e.id} data-grid={{x: e.x, y: e.y, w: e.w, h: e.h}} className="container"><Widget data={e} /></div>
  }
  onAddItem(e) {
      e.preventDefault()
  }
  onSaveGrid(e) {
      e.preventDefault()
  }
  render() {
    let layout = [
      {i: 'a', x: 0, y: 0, w: 1, h: 2, static: true},
      {i: 'b', x: 1, y: 0, w: 3, h: 2, minW: 2, maxW: 4},
      {i: 'c', x: 4, y: 0, w: 1, h: 2}
    ];
    return (
        <div className="container">
          <button className="btn btn-primary" onClick={this.onAddItem}>Add Item</button>
          <button className="btn btn-primary" onClick={this.onSaveGrid}>Save Grid</button>

          <ResponsiveReactGridLayout className="layout" cols={12} rowHeight={30} width={1200}>
              {this.state.widgets.map(this.createElement)}
          </ResponsiveReactGridLayout>
        </div>
    );
  }
}

export default Widgets;
