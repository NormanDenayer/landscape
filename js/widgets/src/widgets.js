import "babel-polyfill";
import React, { Component } from 'react';
import {Panel, Popover, OverlayTrigger, Button, Modal, FormControl, FormGroup,
    HelpBlock, ControlLabel, Alert, ButtonToolbar} from 'react-bootstrap';
import update from 'react-addons-update';
import './widgets.css';
import '../node_modules/react-grid-layout/css/styles.css';
import '../node_modules/react-resizable/css/styles.css';
import $ from 'jquery';
import {Responsive, WidthProvider} from 'react-grid-layout';
const ResponsiveReactGridLayout = WidthProvider(Responsive);

const BASE_API_URL = 'http://127.0.0.1:5001/api/v01';


class Widget extends Component {
  constructor(props) {
      super(props);
      this.state = {dirty: true, content: undefined};
      this._loadContent = this._loadContent.bind(this);
  }
  _loadContent(force) {
      if(!this.state.dirty && !force){
          console.log('not dirty enough');
          return;
      }
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
              dirty: false,
          });
          setTimeout(() => {this._loadContent(true)}, 60000);
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
                      let title = <a href={item.link} target="_blank" onClick={() => this.refs['overlay-' + item.id].hide()}>{item.title}</a>;
                      let popover = <Popover id={'popover-' + item.id} title={title}>{description}</Popover>;
                      return (<div className="row" key={item.id}>
                        <div className={"span4 " + ((item.read)?"read":"")}>
                            <p>
                                {image}
                                <OverlayTrigger ref={'overlay-' + item.id} trigger={['click']} placement="bottom" overlay={popover} rootClose>
                                    <a onClick={() => {
                                        $.ajax({
                                            url: this.props.data.url + '/item/' + item.id,
                                            method: 'POST',
                                            contentType: 'application/json',
                                            servercontentType: 'json',
                                            xhrFields: {withCredentials: true},
                                            context: this,
                                            data: JSON.stringify({read: true})
                                        }).done(() => {
                                            let index = this.state.content.items.findIndex(i => i.id === item.id);
                                            this.setState({content: update(this.state.content, {items: {[index]: {read: {$set: true}}}})});
                                        })
                                    }}>{item.title}</a>
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

class WidgetModal extends Component {
    constructor(props) {
        super(props);
        this.state = {widget: {type: "1", title: "", url: ""}, diff_widget: {}}
    }

    onHide(dirty) {
        if(dirty === true) {
            this.setState({errorText: undefined, widget: {type: "1", title: "", url: ""}, diff_widget: {}});
        }
        if(this.props.onHide) {
            this.props.onHide(dirty)
        }
    }

    onChangeType = (e) => {
        if(this.props.widget !== undefined) {
            this.setState({diff_widget: update(this.state.diff_widget, {type: {$set: e.target.value}})})
        } else {
            this.setState({widget: update(this.state.widget, {type: {$set: e.target.value}})})
        }
    };

    onUrl = (e) => {
        if(this.props.widget !== undefined) {
            this.setState({diff_widget: update(this.state.diff_widget, {url: {$set: e.target.value}})})
        } else {
            this.setState({widget: update(this.state.widget, {url: {$set: e.target.value}})})
        }
    };

    onTitle = (e) => {
        if(this.props.widget !== undefined) {
            this.setState({diff_widget: update(this.state.diff_widget, {title: {$set: e.target.value}})})
        } else {
            this.setState({widget: update(this.state.widget, {title: {$set: e.target.value}})})
        }
    };

    render() {
        let create_flag = true;
        let widget = this.state.widget;
        if(this.state.widget.url === "" && this.props.widget) {
            widget = Object.assign({}, this.props.widget);
            if(this.state.diff_widget.title) widget.title = this.state.diff_widget.title;
            if(this.state.diff_widget.url) widget.url = this.state.diff_widget.url;
            if(this.state.diff_widget.type) widget.type = this.state.diff_widget.type;
            widget.url = widget.uri;
            create_flag = false;
        }
        return <Modal show={this.props.show}>
              <Modal.Header>
                  <Modal.Title>{create_flag?"New widget":"Edit " + widget.title}</Modal.Title>
              </Modal.Header>
              <Modal.Body>
                  {this.state.errorText?<Alert bsStyle="danger">
                      <h3>Oh snap!</h3>
                      <p>{this.state.errorText}</p>
                    </Alert>:""}
                  <FormGroup controlId="type">
                      <ControlLabel>Type</ControlLabel>
                      <FormControl componentClass="select" value={widget.type} onChange={this.onChangeType}>
                          <option value="1">Feed</option>
                          <option value="2">Link</option>
                          <option value="3">Todo</option>
                      </FormControl>
                  </FormGroup>
                  <FieldGroup id="title" label="Title (optional)" type="text" value={widget.title} onChange={this.onTitle} placeholder="Title" />
                  <FieldGroup id="url" label="Url" type="text" value={widget.url} onChange={this.onUrl} placeholder="Url" />
              </Modal.Body>
              <Modal.Footer>
                  <Button bsStyle="primary" onClick={() => {
                      if(create_flag) {  // create
                          $.ajax({
                              url: BASE_API_URL + '/user/' + this.props.user_id + '/widgets',
                              method: 'CREATE',
                              contentType: 'application/json',
                              servercontentType: 'json',
                              xhrFields: {withCredentials: true},
                              context: this,
                              data: JSON.stringify({widget: this.state.widget})
                          }).done(function () {
                              this.onHide(true);
                          }).fail(function (xhr, exception) {
                              this.setState({errorText: xhr.status});
                          })
                      } else {  // update
                          $.ajax({
                              url: BASE_API_URL + '/user/' + this.props.user_id + '/widget/' + widget.id,
                              method: 'POST',
                              contentType: 'application/json',
                              servercontentType: 'json',
                              xhrFields: {withCredentials: true},
                              context: this,
                              data: JSON.stringify({widget: widget})
                          }).done(function () {
                              this.onHide(true);
                          }).fail(function (xhr, exception) {
                              this.setState({errorText: xhr.status});
                          })
                      }
                  }}>{create_flag?"Add":"Update"}</Button>
                  <Button bsStyle="default" onClick={() => this.onHide(false)}>Cancel</Button>
              </Modal.Footer>
          </Modal>
    }
}

class Widgets extends Component {
  constructor(props) {
      super(props);
      this.state = {widgets: [], layout: {}, showAddWidget: false, widget:undefined,
          showLogin: false, username: undefined, password: undefined,
          errorText: undefined, user_id: undefined};
  }
  componentDidMount() {
      this.loadGrid();
  }
  loadGrid = () => {
      $.ajax({
          url: BASE_API_URL + '/user/' + this.state.user_id + '/widgets',
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
                      w.i = w.id.toString();
                      return w;
                  })
              })
          }
      }).fail((xhr) => {
          if(xhr.status === 401 || xhr.status === 0 || xhr.status === 403) {
              this.setState({showLogin: true})
          }
          console.error('-> login');
      });
  };
  onRemoveItem = (el) => {
      this.setState({widgets: this.state.widgets.filter(w => w.id !== el.id)});
  };
  onUpdateItem = (el) => {
      this.setState({
          widget: el,
          showAddWidget: true,
      })
  };
  createElement = (e) => {
      return <div key={e.id}>
          <Widget key={e.id} data={e} />
          <span className="remove glyphicon glyphicon-erase" onClick={this.onRemoveItem.bind(this, e)} />
          <span className="update glyphicon glyphicon-pencil" onClick={this.onUpdateItem.bind(this, e)} />
      </div>
  };
  onAddItem = (e) => {
      e.preventDefault();
      this.setState({showAddWidget: true});
  };
  onSaveGrid = (e) => {
      e.preventDefault();
      $.ajax({
          url: BASE_API_URL + '/user/' + this.state.user_id + '/widgets',
          method:'POST',
          servercontentType: 'json',
          dataType: 'json',
          contentType: 'application/json',
          data: JSON.stringify({'widgets': this.state.layout}),
          xhrFields: {withCredentials: true},
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
  mobileLayout = (layout) => {
      return layout.map((l) => {
          let i = Object.assign({}, l);
          i.x = 0;
          return i;
      });
  };
  render() {
    let layout = this.state.widgets;
    let mobLayout = this.mobileLayout(layout);
    console.log(layout);
    return (
        <div className="container">

          <ResponsiveReactGridLayout className="layout"
                                     rowHeight={30} measureBeforeMount={false}
                                     cols={{lg: 12, md: 10, sm: 6, xs: 4, xxs: 2}}
                                     breakpoints={{lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0}}
                                     layouts={{lg: layout, md: layout, sm: mobLayout, xs: mobLayout, xxs: mobLayout}}
                                     onLayoutChange={this.onLayoutChange}>
              {this.state.widgets.map(this.createElement)}
          </ResponsiveReactGridLayout>
          <hr />
          <ButtonToolbar>
            <Button bsStyle="primary" onClick={this.onAddItem}>Add Item</Button>
            <Button bsStyle="primary" onClick={this.onSaveGrid}>Save Grid</Button>
            <Button bsStyle="primary" onClick={() => {
                $.ajax({
                    url: BASE_API_URL + '/logout',
                    method: 'get',
                    contentType: 'application/json',
                    xhrFields: {withCredentials: true},
                    context: this
                }).done(function(){
                    this.setState({username: undefined, password: undefined, showLogin: true, errorText: undefined});
                })
            }}>Logout</Button>
          </ButtonToolbar>

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
                  <Button bsStyle="primary" onClick={() => {
                      $.ajax({
                          url: BASE_API_URL + '/login',
                          method: 'post',
                          contentType: 'application/json',
                          servercontentType: 'json',
                          xhrFields: {withCredentials: true},
                          context: this,
                          data: JSON.stringify({username: this.state.username, password: this.state.password})
                      }).done(function(resp){
                          this.setState({username: undefined, password: undefined, showLogin: false, errorText: undefined, user_id: resp.user_d});
                          this.loadGrid();
                      }).fail(function(){
                          this.setState({errorText: "Invalid credentials..."});
                      })
                  }}>Sign in</Button>
              </Modal.Footer>
          </Modal>
          <WidgetModal show={this.state.showAddWidget} widget={this.state.widget} user_id={this.state.user_id} onHide={(dirty) => {
              if(dirty) {
                  this.loadGrid();
              }
              this.setState({showAddWidget: false, widget: undefined});
          }}/>
        </div>
    );
  }
}

export default Widgets;
