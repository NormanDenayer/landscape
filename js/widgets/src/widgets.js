import "babel-polyfill";
import React, { Component } from 'react';

import Panel from 'react-bootstrap/lib/Panel';
import Popover from 'react-bootstrap/lib/Popover';
import OverlayTrigger from 'react-bootstrap/lib/OverlayTrigger';
import Button from 'react-bootstrap/lib/Button';
import ButtonToolbar from 'react-bootstrap/lib/ButtonToolbar';
import Modal from 'react-bootstrap/lib/Modal';
import Form from 'react-bootstrap/lib/Form';
import FormControl from 'react-bootstrap/lib/FormControl';
import FormGroup from 'react-bootstrap/lib/FormGroup';
import HelpBlock from 'react-bootstrap/lib/HelpBlock';
import ControlLabel from 'react-bootstrap/lib/ControlLabel';
import Alert from 'react-bootstrap/lib/Alert';

import update from 'react-addons-update';
import './widgets.css';
import '../node_modules/react-grid-layout/css/styles.css';
import '../node_modules/react-resizable/css/styles.css';
import $ from 'jquery';
import {Responsive, WidthProvider} from 'react-grid-layout';
const ResponsiveReactGridLayout = WidthProvider(Responsive);

const API_URL_PREFIX = process.env.NODE_ENV === 'production'?window.location.origin:'http://127.0.0.1:5001';
const BASE_API_URL = API_URL_PREFIX + '/api/v01';


class Widget extends Component {
  constructor(props) {
      super(props);
      this.state = {dirty: true, content: null};
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
                  title: resp.widget.content.channel?resp.widget.content.channel.title:resp.widget.title,
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
      if(this.state.content === null) {
          return (<div className="container-fluid" style={{height: "inherit"}}>
              <Panel header='*none*' bsStyle="info">
                  <div className="container-fluid">
                  </div>
              </Panel>
          </div>);
      }

      return (<div className="container-fluid" style={{height: "inherit"}}>
          <Panel header={this.state.content.title || "<title>"} bsStyle="info">
              <div className="container-fluid" onMouseDown={ e => e.stopPropagation() }>
                  {this.state.content.items.map((item) => {
                      let image = '';
                      let image_desc = '';
                      let pub_time = new Date(item.at);

                      if(item.picture) {
                        image = (<img style={{float:"left", marginBottom:"2px"}} width="40" src={item.picture} alt="" />);
                        image_desc = (<img style={{float:"left", marginRight:"2px", marginBottom:"2px"}} width="100" src={item.picture} alt="" />);
                      }
                      let description = (<div className="media">
                          {image_desc}
                          <p>{item.description}</p>
                          <p>Published at: {pub_time.toString()}</p>
                        </div>);
                      let title = (<a href={item.link} target="_blank" onClick={() => this.refs['overlay-' + item.id].hide()}>{item.title}</a>);
                      let popover = (<Popover id={'popover-' + item.id} title={title}>{description}</Popover>);
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
                      </div>)
                  })}
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

class NewWidgetModal extends Component {
    constructor(props) {
        super(props);
        this.state = {widget: {type: 1, title: "", url: "", content: {}}, diff_widget: {content: {}}};
        this.onHide = this.onHide.bind(this);
        this.onChangeType = this.onChangeType.bind(this);
        this.onUrl = this.onUrl.bind(this);
        this.onTitle = this.onTitle.bind(this);
        this.onUsername = this.onUsername.bind(this);
        this.onPassword = this.onPassword.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    onHide(dirty) {
        if(dirty === true) {
            this.setState({errorText: undefined, widget: {type: "1", title: "", url: "", content: {}}, diff_widget: {content: {}}});
        }
        this.props.onHide && this.props.onHide(dirty);
    }

    onChangeType(e){
        this.setState({widget: update(this.state.widget, {type: {$set: parseInt(e.target.value, 10)}})})
    }

    onUrl(e){
        this.setState({widget: update(this.state.widget, {url: {$set: e.target.value}})})
    }

    onTitle(e){
        this.setState({widget: update(this.state.widget, {title: {$set: e.target.value}})})
    }

    onUsername(e) {
        this.setState({widget: update(this.state.widget, {content: {username: {$set: e.target.value}}})})
    }

    onPassword(e) {
        this.setState({widget: update(this.state.widget, {content: {password: {$set: e.target.value}}})})
    }

    onSubmit(e) {
        e.preventDefault();

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
    }

    render() {
        let create_flag = true;
        let widget = this.state.widget;
        if(this.state.widget.url === "" && this.props.widget) {
            widget = Object.assign({}, this.props.widget);
            if(this.state.diff_widget.title) widget.title = this.state.diff_widget.title;
            if(this.state.diff_widget.url) widget.url = this.state.diff_widget.url;
            if(this.state.diff_widget.type) widget.type = this.state.diff_widget.type;
            if(this.state.diff_widget.content.username) widget.content.username = this.state.diff_widget.content.username;
            if(this.state.diff_widget.content.password) widget.content.password = this.state.diff_widget.content.password;
            widget.url = widget.uri;
            create_flag = false;
        }
        let alert = '';
        if(this.state.errorText) {
            alert = <Alert bsStyle="danger">
                      <h3>Oh snap!</h3>
                      <p>{this.state.errorText}</p>
                    </Alert>;
        }

        const default_fields = [
            <FieldGroup id="title" label="Title (optional)" type="text" value={widget.title} onChange={this.onTitle} placeholder="Title" />,
            <FieldGroup id="url" label="Url" type="text" value={widget.url} onChange={this.onUrl} placeholder="Url" />
        ];
        const credential_fields = [
            <FieldGroup id="username" label="Username" type="text" value={widget.content.username} onChange={this.onUsername} />,
            <FieldGroup id="password" label="Password" type="password" value={widget.content.password} onChange={this.onPassword} />
        ];
        const TYPES = [
            {value:1, name:'Feed', fields: default_fields},
            {value:2, name:'Link', fields: default_fields},
            {value:3, name:'Todo', fields: default_fields},
            {value:4, name:'Espace Famille', fields: credential_fields},
        ];
        const TYPE = TYPES.find(t => t.value === widget.type);
        return <Modal show={this.props.show}>
              <Modal.Header>
                  <Modal.Title>{create_flag?"New widget":"Edit " + widget.title}</Modal.Title>
              </Modal.Header>
              <Modal.Body>
                  {alert}
                  <FormGroup controlId="type">
                      <ControlLabel>Type</ControlLabel>
                      <FormControl componentClass="select" value={widget.type} onChange={this.onChangeType}>
                      {
                          TYPES.map(t => <option key={t.value} value={t.value}>{t.name}</option>)
                      }
                      </FormControl>
                  </FormGroup>
                  {
                      TYPE && TYPE.fields.map((f, i) => <div key={i}>{f}</div>)
                  }
              </Modal.Body>
              <Modal.Footer>
                  <Button bsStyle="primary" onClick={this.onSubmit}>{create_flag?"Add":"Update"}</Button>
                  <Button bsStyle="default" onClick={() => this.onHide(false)}>Cancel</Button>
              </Modal.Footer>
          </Modal>
    }
}

class UpdateWidgetModal extends NewWidgetModal {
    onChangeType(e){
        this.setState({diff_widget: update(this.state.diff_widget, {type: {$set: e.target.value}})})
    }

    onUrl(e){
        this.setState({diff_widget: update(this.state.diff_widget, {url: {$set: e.target.value}})})
    }

    onTitle(e){
        this.setState({diff_widget: update(this.state.diff_widget, {title: {$set: e.target.value}})})
    }

    onUsername(e) {
        this.setState({diff_widget: update(this.state.widget, {content: {username: {$set: e.target.value}}})})
    }

    onPassword(e) {
        this.setState({diff_widget: update(this.state.widget, {content: {password: {$set: e.target.value}}})})
    }

    onSubmit(e) {
        e.preventDefault();

        $.ajax({
            url: BASE_API_URL + '/user/' + this.props.user_id + '/widget/' + this.state.widget.id,
            method: 'POST',
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
    }
}

class Widgets extends Component {
  constructor(props) {
      super(props);
      this.state = {widgets: [], layout: {}, showAddWidget: false, showUpdateWidget: false, widget:undefined,
          showLogin: false, username: undefined, password: undefined, loging_in: false,
          errorText: undefined, user_id: undefined};
      this.loadGrid = this.loadGrid.bind(this);
      this.onRemoveItem = this.onRemoveItem.bind(this);
      this.onAddItem = this.onAddItem.bind(this);
      this.onUpdateItem = this.onUpdateItem.bind(this);
      this.onSaveGrid = this.onSaveGrid.bind(this);
      this.onLayoutChange = this.onLayoutChange.bind(this);
      this.mobileLayout = this.mobileLayout.bind(this);
      this.createElement = this.createElement.bind(this);
  }

  componentDidMount() {
      this.loadGrid();
  }

  loadGrid() {
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
  }

  onRemoveItem(el){
      this.setState({widgets: this.state.widgets.filter(w => w.id !== el.id)});
  }

  onUpdateItem(el){
      this.setState({
          widget: el,
          showUpdateWidget: true,
      })
  }

  createElement(e){
      return <div key={e.id}>
          <Widget key={e.id} data={e} />
          <span className="remove glyphicon glyphicon-erase" onClick={this.onRemoveItem.bind(this, e)} />
          <span className="update glyphicon glyphicon-pencil" onClick={this.onUpdateItem.bind(this, e)} />
      </div>
  }

  onAddItem(e) {
      e.preventDefault();
      this.setState({showAddWidget: true});
  }

  onSaveGrid(e) {
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
  }

  onLayoutChange(layout) {
      this.setState({layout: layout});
      console.log(layout);
  }

  mobileLayout(layout) {
      return layout.map((l) => {
          let i = Object.assign({}, l);
          i.x = 0;
          return i;
      });
  }

  render() {
    let layout = this.state.widgets;
    let mobLayout = this.mobileLayout(layout);
    //console.log(layout);
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
              <Form>
                  <Modal.Header><Modal.Title>Login required</Modal.Title></Modal.Header>
                  <Modal.Body>
                      {this.state.errorText && (
                          <Alert bsStyle="danger">
                            <h3>Oh snap!</h3>
                            <p>{this.state.errorText}</p>
                          </Alert>
                      )}
                      <FieldGroup id="username" label="Username" type="text" value={this.state.username} onChange={(e) => {this.setState({username: e.target.value})}} placeholder="Username" />
                      <FieldGroup id="password" label="Password" type="password" value={this.state.password} onChange={(e) => {this.setState({password: e.target.value})}} placeholder="Password" />
                  </Modal.Body>
              <Modal.Footer>
                  <Button bsStyle="primary" type="submit" disabled={this.state.loging_in} onClick={e => {
                      e.preventDefault();
                      $.ajax({
                          url: BASE_API_URL + '/login',
                          method: 'post',
                          contentType: 'application/json',
                          servercontentType: 'json',
                          //xhrFields: {withCredentials: true},
                          context: this,
                          data: JSON.stringify({username: this.state.username, password: this.state.password})
                      }).done(function(resp){
                          this.setState({loging_in: false, username: undefined, password: undefined, showLogin: false, errorText: undefined, user_id: resp.user_id});
                          this.loadGrid();
                      }).fail(function(){
                          this.setState({loging_in: false, errorText: "Invalid credentials..."});
                      })
                      this.setState({loging_in: true});
                  }}>Sign in</Button>
              </Modal.Footer>
              </Form>
          </Modal>
          <NewWidgetModal show={this.state.showAddWidget} user_id={this.state.user_id} onHide={dirty => {
              dirty && this.loadGrid();
              this.setState({showAddWidget: false});
          }}/>
          <UpdateWidgetModal show={this.state.showUpdateWidget} widget={this.state.widget} user_id={this.state.user_id} onHide={dirty => {
              dirty && this.loadGrid();
              this.setState({showUpdateWidget: false, widget: undefined});
          }}/>
        </div>
    );
  }
}

export default Widgets;
