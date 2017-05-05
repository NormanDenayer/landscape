import "babel-polyfill";
import React, { Component } from 'react';
import {Panel, Popover, OverlayTrigger, Button, Modal, FormControl, FormGroup,
    HelpBlock, ControlLabel, Alert} from 'react-bootstrap';
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
          xhrFields: {withCredentials: true},
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
          console.error('fail to fetch: ' + this.props.data.url);
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
                        image = <img style={{float:"left", marginBottom:"2px"}} width="40" src={item.picture} alt="" />;
                        image_desc = <img style={{float:"left", marginRight:"2px", marginBottom:"2px"}} width="100" src={item.picture} alt="" />;
                      }
                      let description = (<div className="media">
                          {image_desc}
                          <p>{item.description}</p>
                          <p>Published at: {item.at}</p>
                        </div>);
                      let title = <a href={item.link} target="_blank" onClick={() => this.refs['overlay-' + item.i].hide()}>{item.title}</a>;
                      let popover = <Popover title={title}>{description}</Popover>;
                      return (<div className="row">
                        <div className="span4">
                            <p>
                                {image}
                                <OverlayTrigger ref={'overlay-' + item.i} trigger={['click']} placement="bottom" overlay={popover} rootClose>
                                    <a>{item.title}</a>
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

function FieldGroup({ id, label, help, ...props }) {
  return (
    <FormGroup controlId={id}>
      <ControlLabel>{label}</ControlLabel>
      <FormControl {...props} />
      {help && <HelpBlock>{help}</HelpBlock>}
    </FormGroup>
  );
}

class Widgets extends Component {
  constructor(props) {
      super(props);
      this.state = {widgets: [], layout: {}, showLogin: false, username: undefined, password: undefined, errorText: undefined};
  }
  componentDidMount() {
      this.loadGrid();
  }
  loadGrid = () => {
      $.ajax({
          url: 'http://127.0.0.1:5000/api/v01/user/1/widgets',
          method:'GET',
          servercontentType: 'json',
          xhrFields: {withCredentials: true},
          context: this
      }).done(function(resp, statusText, xhr){
          if(xhr.status === 200) {
              this.setState({
                  widgets: resp.widgets.map((w) => {
                      w.w = w.width;
                      w.h = w.height;
                      return w;
                  })
              })
          }
      }).fail(function(xhr, exception){
          if(xhr.status === 401) {
              this.setState({showLogin: true})
          }
          console.error('-> login');
      });
  };
  onRemoveItem = (el) => {
      this.setState({widgets: this.state.widgets.filter(w => w.id !== el.id)});
      console.log('removing an item');
  };
  createElement = (e) => {
      let removeStyle = {
          position: 'absolute',
          right: '30px',
          top: '5px',
          cursor: 'pointer'
      };
      console.log(e);
      return <div key={e.id} data-grid={e}>
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
      }).done(function(){
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

          <ResponsiveReactGridLayout className="layout"
                                     cols={12}
                                     rowHeight={30}
                                     width={1200}
                                     onLayoutChange={this.onLayoutChange}>
              {this.state.widgets.map(this.createElement)}
          </ResponsiveReactGridLayout>
          <hr />
          <button className="btn btn-primary" onClick={this.onAddItem}>Add Item</button>
          <button className="btn btn-primary" onClick={this.onSaveGrid}>Save Grid</button>

          <Modal show={this.state.showLogin}>
              <Modal.Header><Modal.Title>Login required</Modal.Title></Modal.Header>
              <Modal.Body>
                  {this.state.errorText?<Alert bsStyle="danger">
                      <h3>Oh snap!</h3>
                      <p>{this.state.errorText}</p>
                    </Alert>:""}
                  <FieldGroup id="username" label="Username" type="text" value={this.state.username} onChange={(e) => {this.setState({username: e.target.value})}} placeholder="Username" />
                  <FieldGroup id="password" label="Password" type="password" value={this.state.password} onChange={(e) => {this.setState({password: e.target.value})}} placeholder="Password" />
              </Modal.Body>
              <Modal.Footer>
                  <Button onClick={() => {
                      $.ajax({
                          url: 'http://127.0.0.1:5000/api/v01/login',
                          method: 'post',
                          contentType: 'application/json',
                          context: this,
                          data: JSON.stringify({username: this.state.username, password: this.state.password})
                      }).done(function(){
                          this.setState({username: undefined, password: undefined, showLogin: false, errorText: undefined});
                          this.loadGrid();
                      }).fail(function(){
                          this.setState({errorText: "Invalid credentials..."});
                      })
                  }}>Sign in</Button>
              </Modal.Footer>
          </Modal>

        </div>
    );
  }
}

export default Widgets;
