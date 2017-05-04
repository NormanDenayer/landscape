import "babel-polyfill";
import React, { Component } from 'react';
import {Panel, Popover, OverlayTrigger} from 'react-bootstrap';
import './widgets.css';
import '../node_modules/react-grid-layout/css/styles.css';
import '../node_modules/react-resizable/css/styles.css';
import $ from 'jquery';
import ResponsiveReactGridLayout from 'react-grid-layout';


class Widget extends Component {
  constructor(props) {
      super(props);
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
          console.log(resp);
          this.setState({
              content: {
                  title: resp.widget.content.channel.title,
                  items: resp.widget.content.items,
              },
          });
          setTimeout(this._loadContent, 60000);
      }).fail(function() {
          console.log('fail to fetch: ' + this.props.data.url);
          setTimeout(this._loadContent, 60000);
      });
  }
  componentDidMount() {
      this._loadContent();
  }
  render() {
      if(this.state.content === undefined) {
          return (<div className="container-fluid" style={{height: "inherit"}}>
              <Panel header='*none*' bsStyle="info">
                  <div className="container-fluid">
                  </div>
              </Panel>
          </div>);
      }

      return (<div className="container-fluid" style={{height: "inherit"}}>
          <Panel header={this.state.content.title} bsStyle="info">
              <div className="container-fluid" onMouseDown={ e => e.stopPropagation() }>
                  {this.state.content.items.map((item) => {
                      let image = '';
                      let image_desc = '';

                      if(item.picture) {
                        image = <img style={{float:"left"}} width="40" align="left" hspace="2" vspace="2" src={item.picture} alt="" />;
                        image_desc = <img style={{float:"left"}} width="100" align="left" hspace="2" vspace="2" src={item.picture} alt="" />;
                      }
                      let description = (<div className="media">
                          {image_desc}
                          <p>{item.description}</p>
                          <p>Published at: {item.at}</p>
                        </div>);

                      let popover = <Popover title={item.title}>{description}</Popover>;
                      return (<div className="row">
                        <div className="span4">
                            <p>
                                {image}
                                <OverlayTrigger trigger={['hover', 'focus']} placement="bottom" overlay={popover}>
                                    <a href={item.link} target="_blank">{item.title}</a>
                                </OverlayTrigger>
                            </p>
                        </div>
                      </div>);
                  })};
              </div>
          </Panel>
      </div>)
  }
}

class Widgets extends Component {
  constructor(props) {
      super(props);
      this.state = {widgets: [], layout: {}};
  }
  componentDidMount() {
      this.loadGrid();
  }
  loadGrid = () => {
      $.ajax({
          url: 'http://127.0.0.1:5000/api/v01/user/1/widgets',
          method:'GET',
          servercontentType: 'json',
          context: this
      }).done(function(resp){
          this.setState({widgets: resp.widgets.map((w) => {w.w = w.width; w.h = w.height; return w;})})
      }.bind(this)).fail(function(){
          let fakeConfig = {"widgets":[{"h":3,"id":1,"type":1,"url":"/api/v01/user/1/widget/1","w":5,"x":1,"y":0},{"h":3,"id":2,"type":1,"url":"/api/v01/user/1/widget/2","w":5,"x":0,"y":4},{"h":3,"id":3,"type":1,"url":"/api/v01/user/1/widget/3","w":5,"x":0,"y":8},{"h":3,"id":4,"type":1,"url":"/api/v01/user/1/widget/4","w":5,"x":0,"y":12},{"h":3,"id":5,"type":1,"url":"/api/v01/user/1/widget/5","w":5,"x":0,"y":16},{"h":3,"id":6,"type":1,"url":"/api/v01/user/1/widget/6","w":5,"x":0,"y":20}]};
          this.setState({widgets: fakeConfig.widgets})
      }.bind(this));
  };
  onRemoveItem = (el) => {
      console.log('removing an item');
  };
  createElement = (e) => {
      let removeStyle = {
          position: 'absolute',
          right: '2px',
          top: 0,
          cursor: 'pointer'
      };
      console.log(e);
      return <div className="container-fluid" key={e.id} data-grid={e}>
          <Widget data={e} />
          <span className="remove" style={removeStyle} onClick={this.onRemoveItem.bind(this, e)}>x</span>
      </div>
  };
  onAddItem = (e) => {
      e.preventDefault();
      console.log('adding an item')
  };
  onSaveGrid = (e) => {
      e.preventDefault();
      $.ajax({
          url: 'http://127.0.0.1:5000/api/v01/user/1/widgets',
          method:'POST',
          servercontentType: 'json',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify({'widgets': this.state.layout}),
          context: this
      }).done(function(resp){
          console.log('saving the grid')
      }).fail(function(){
          console.error('oups!!!');
      });
  };
  onLayoutChange = (layout) => {
      this.setState({layout: layout});
      console.log(layout);
  };
  render() {
    return (
        <div className="container">

          <ResponsiveReactGridLayout className="layout" cols={12} rowHeight={30} width={1200} onLayoutChange={this.onLayoutChange}>
              {this.state.widgets.map(this.createElement)}
          </ResponsiveReactGridLayout>
          <hr />
          <button className="btn btn-primary" onClick={this.onAddItem}>Add Item</button>
          <button className="btn btn-primary" onClick={this.onSaveGrid}>Save Grid</button>
        </div>
    );
  }
}

export default Widgets;
