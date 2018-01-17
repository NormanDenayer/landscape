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
import Table from 'react-bootstrap/lib/Table';

import {Bar} from 'react-chartjs-2';

import update from 'react-addons-update';
import './widgets.css';
import '../node_modules/react-grid-layout/css/styles.css';
import '../node_modules/react-resizable/css/styles.css';
import {Responsive, WidthProvider} from 'react-grid-layout';
const ResponsiveReactGridLayout = WidthProvider(Responsive);

const API_URL_PREFIX = process.env.NODE_ENV === 'production'?window.location.origin:'http://127.0.0.1:5000';
const BASE_API_URL = API_URL_PREFIX + '/api/v01';


export function parseJSON(response) {
  return response.json()
}

export function checkStatus(response) {
  if (response.status >= 200 && response.status < 300) {
    return response
  } else {
    //let error = null;
    let contentType = response.headers.get("content-type");
    if(contentType && contentType.indexOf("application/json") !== -1) {
        return response.json().then(function(json) {
          const message = json.error || json.errors || response.statusText;
          throw new Error(message);
        });
    }

    let error = new Error(response.statusText);
    error.response = response;
    throw error
  }
}

class WidgetMeteo extends Component {
    constructor(props) {
        super(props);
        this.state = {
            content: undefined, content_error: undefined,
        };
        this.loadContent = this.loadContent.bind(this);
    }

    loadContent() {
        fetch(API_URL_PREFIX + this.props.data.url, {
            method: 'get',
            headers: {
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + this.props.auth_token
            }
        }).then(checkStatus)
        .then(parseJSON)
        .then(data => {
            this.setState({content_error: undefined, content: JSON.parse(data.widget.content), lastUpdate: data.widget.updated_on});
            setTimeout(() => this.loadContent(true), 5 * 60 * 1000);
        })
        .catch(error => {
            console.error(error);
            this.setState({content_error: error});
            setTimeout(() => this.loadContent(true), 15 * 60 * 1000);
        });
    }

    componentDidMount() {
        this.loadContent();
    }

    render() {
        if(this.state.content === undefined) {
            return (
            <div className="container-fluid" style={{height: "inherit"}}>
                <Panel header="Loading..." bsStyle="info">
                    <div className="container-fluid" />
                </Panel>
            </div>
            )
        }

        if(this.state.content_error !== undefined) {
            return (
            <div className="container-fluid" style={{height: "inherit"}}>
                <Panel header="Loading..." bsStyle="info">
                    <div className="container-fluid">
                        <Alert bsStyle="danger" >{this.state.content_error.message}</Alert>
                    </div>
                </Panel>
            </div>
            )
        }

        let timestamps = [];
        for (let i = 0; i <= this.state.content.rain_risk_levels.length; i++) {
            timestamps.push("" + i * 5 + "min");
        }

        const data = {
          labels: timestamps,
          datasets: [
              {
                  //label: 'Rain Risk Level',
                  backgroundColor: 'rgba(255,99,132,0.2)',
                  //borderColor: 'rgba(255,99,132,1)',
                  //borderWidth: 1,
                  hoverBackgroundColor: 'rgba(255,99,132,0.4)',
                  hoverBorderColor: 'rgba(255,99,132,1)',
                  data: this.state.content.rain_risk_levels.map(l => ({y: l.y, label: l.label})),
              }
          ]
        };

        const p = this.state.content.previsions;
        return (<div className="container-fluid" style={{height: "inherit"}}>
          <Panel header={"Meteo for " + this.state.content.city + " (" + this.state.lastUpdate + ")"} bsStyle="info">
              <div className="container-fluid" onMouseDown={ e => e.stopPropagation() }>
                  <Bar
                      options={{
                          tooltips: {
                              callbacks: {
                                  label: (item, data) => data.datasets[0].data[item.index].label
                              }
                          },
                          legend: {display: false},
                          scales: {
                              yAxes: [{
                                  ticks: {
                                      beginAtZero: 0,
                                      max: 5
                                  }
                              }]
                          }
                      }}
                      height={50}
                      width={150}
                      data={data} />
                  <hl />
                  <i>Previsions</i>
                  <Table>
                      <thead>
                          <tr>
                              <th>Day</th>
                              <th>Time</th>
                              <th>Sum.</th>
                              <th>Temp.</th>
                          </tr>
                      </thead>
                      <tbody>
                      {
                          Object.keys(p).map(day => (
                              Object.keys(p[day]).map(start_slice => (
                                  <tr>
                                      <td>{day}</td>
                                      <td>{start_slice}</td>
                                      <td>{p[day][start_slice][1]}</td>
                                      <td>{p[day][start_slice][0]}</td>
                                  </tr>
                              ))
                          ))
                      }
                      </tbody>
                  </Table>
              </div>
          </Panel>
      </div>)
    }
}

class Widget extends Component {
  constructor(props) {
      super(props);
      this.state = {dirty: true, items: null, title: null};
      this._loadContent = this._loadContent.bind(this);
      this.onItemClick = this.onItemClick.bind(this);
  }

  _loadContent(force) {
      if(!this.state.dirty && !force){
          console.log('not dirty enough');
          return;
      }
      fetch(API_URL_PREFIX + this.props.data.url, {
          method: 'get',
          headers: {
              'Accept': 'application/json',
              'Authorization': 'Bearer ' + this.props.auth_token
          }
      }).then(checkStatus)
      .then(parseJSON)
      .then(data => {
          let content = JSON.parse(data.widget.content);
          let title = content.channel?content.channel.title:data.widget.title;
          if(data.widget.updated_on) {
              title += ' (' + data.widget.updated_on + ')'
          }
          this.setState({
              dirty: false,
              title: title,
              items: content.items,
          });
          setTimeout(() => this._loadContent(true), 60 * 1000);
      })
      .catch(error => {
          console.error(error);
          setTimeout(() => this._loadContent(true), 15 * 60 * 1000);
      });
  }

  componentDidMount() {
      this._loadContent();
  }

  onItemClick(item) {
      fetch(API_URL_PREFIX + this.props.data.url + '/item/' + item.id, {
          method: 'post',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + this.props.auth_token
          },
          body: JSON.stringify({read: true})
      }).then(checkStatus)
      .then(() => {
          let index = this.state.items.findIndex(i => i.id === item.id);
          this.setState({items: update(this.state.items, {[index]: {read: {$set: true}}})});
      });
  }

  render() {
      if(this.state.items === null) {
          return (<div className="container-fluid" style={{height: "inherit"}}>
              <Panel header='Loading...' bsStyle="info">
                  <div className="container-fluid" />
              </Panel>
          </div>);
      }

      return (<div className="container-fluid" style={{height: "inherit"}}>
          <Panel header={this.state.title || "<title>"} bsStyle="info">
              <div className="container-fluid" onMouseDown={ e => e.stopPropagation() }>
                  {this.state.items.map((item, i) => {
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
                      return (<div className="row" key={i}>
                        <div className={"span4 " + ((item.read)?"read":"")}>
                            <p>
                                {image}
                                <OverlayTrigger ref={'overlay-' + item.id} trigger={['click']} placement="bottom" overlay={popover} rootClose>
                                    <a onClick={() => this.onItemClick(item)}>{item.title}</a>
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
        this.onCity = this.onCity.bind(this);
        this.onZip = this.onZip.bind(this);
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

    onCity(e) {
        this.setState({widget: update(this.state.widget, {content: {city: {$set: e.target.value}}})})
    }

    onZip(e) {
        this.setState({widget: update(this.state.widget, {content: {zip_code: {$set: e.target.value}}})})
    }

    onSubmit(e) {
        e.preventDefault();

        fetch(BASE_API_URL + '/user/' + this.props.user_id + '/widgets', {
            method: 'post',
            headers: {
                'Authorization': 'Bearer ' + this.props.auth_token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({widget: this.state.widget})
        }).then(checkStatus)
        .then(() => this.onHide(true))
        .catch(error => this.setState({errorText: error.message}));
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
            if(this.state.diff_widget.content.city) widget.content.city = this.state.diff_widget.content.city;
            if(this.state.diff_widget.content.zip_code) widget.content.zip_code = this.state.diff_widget.content.zip_code;
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
        const meteo_fields = [
            <FieldGroup id="city" label="City" type="text" value={widget.content.city} onChange={this.onCity} />,
            <FieldGroup id="zip_code" label="Zip" type="text" value={widget.content.zip_code} onChange={this.onZip} />,
        ];
        const TYPES = [
            {value:1, name:'Feed', fields: default_fields},
            //{value:2, name:'Link', fields: default_fields},
            //{value:3, name:'Todo', fields: default_fields},
            {value:4, name:'Espace Famille', fields: credential_fields},
            {value:5, name:'Meteo France', fields: meteo_fields}
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

    onCity(e) {
        this.setState({diff_widget: update(this.state.widget, {content: {city: {$set: e.target.value}}})})
    }

    onZip(e) {
        this.setState({diff_widget: update(this.state.widget, {content: {zip_code: {$set: e.target.value}}})})
    }

    onSubmit(e) {
        e.preventDefault();

        fetch(BASE_API_URL + '/user/' + this.props.user_id + '/widget/' + this.state.widget.widget_id, {
            method: 'post',
            headers: {
                'Authorization': 'Bearer ' + this.props.auth_token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({widget: this.state.widget})
        }).then(checkStatus)
        .then(() => this.onHide(true))
        .catch(error => this.setState({errorText: error.message}));
    }
}

function setCookie(cname, cvalue, exdays) {
    let d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    const expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    const name = cname + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

class Widgets extends Component {
  constructor(props) {
      super(props);
      this.state = {widgets: [], layout: {}, showAddWidget: false, showUpdateWidget: false, widget:undefined,
          showLogin: false, username: undefined, password: undefined, loging_in: false, widgetsError: undefined,
          errorText: undefined, user_id: undefined, loginError: undefined, user: undefined};
      this.loadGrid = this.loadGrid.bind(this);
      this.onRemoveItem = this.onRemoveItem.bind(this);
      this.onAddItem = this.onAddItem.bind(this);
      this.onUpdateItem = this.onUpdateItem.bind(this);
      this.onSaveGrid = this.onSaveGrid.bind(this);
      this.onLayoutChange = this.onLayoutChange.bind(this);
      this.mobileLayout = this.mobileLayout.bind(this);
      this.createElement = this.createElement.bind(this);
  }

  // get the user info out from local cookie (if possible)
  componentDidMount() {
      let value = getCookie("user");
      if(value) {
          this.setState({user: JSON.parse(value)});
          setTimeout(this.loadGrid, 500);
      }
  }

  loadGrid() {
      this.setState({widgetsError: undefined});
      fetch(BASE_API_URL + '/user/' + this.state.user.id + '/widgets', {
          method: 'get',
          headers: {
              'Accept': 'application/json',
              'Authorization': 'Bearer ' + this.state.user.token
          }
      }).then(checkStatus)
      .then(parseJSON)
      .then(data => {
          this.setState({widgets: data.widgets.map(w => {
                  w.w = w.width;
                  w.h = w.height;
                  w.i = w.widget_id.toString();
                  return w;
              })})
      })
      .catch(error => {
          if(error.response && (error.response.status === 401 || error.response.status === 403)) {
              this.setState({widgetsError: error})
          }
      });
  }

  onRemoveItem(el){
      let confirm_ = confirm('Are you sure you want to delete this widget?');
      if(confirm_ !== true) {
          return
      }
      this.setState({widgets: this.state.widgets.filter(w => w.widget_id !== el.widget_id)});
      fetch(BASE_API_URL + '/user/' + this.state.user.id + '/widget/' + el.widget_id, {
          method: 'delete',
          headers: {
              'Authorization': 'Bearer ' + this.state.user.token
          }
      }).then(checkStatus)
      .then(() => this.setState({widgetDeleted: true}))
      .catch(error => this.setState({widgetDelError: error}))
  }

  onUpdateItem(el){
      this.setState({
          widget: el,
          showUpdateWidget: true,
      })
  }

  createElement(e){
      let widget = null;
      switch(e.type) {
          case 'METEO_FRANCE':
              widget = <WidgetMeteo key={e.widget_id} data={e} auth_token={this.state.user.token} />;
              break;
          default:
              widget = <Widget key={e.widget_id} data={e} auth_token={this.state.user.token} />
      }
      return <div key={e.widget_id}>
          {widget}
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
      this.setState({gridSaved: false, gridSaveError: undefined});
      fetch(BASE_API_URL + '/user/' + this.state.user.id + '/widgets', {
          method: 'put',
          headers: {
              'Accept': 'application/json',
              'Authorization': 'Bearer ' + this.state.user.token
          },
          body: JSON.stringify({'widgets': this.state.layout})
      }).then(checkStatus)
      .then(() => this.setState({gridSaved: true}))
      .catch(error => this.setState({gridSaveError: error}))
  }

  onLayoutChange(layout) {
      this.setState({layout: layout});
      console.log(layout);
  }

  mobileLayout(layout) {
      return layout.map(l => {
          let i = Object.assign({}, l);
          i.x = 0;
          return i;
      });
  }

  render() {
    if(this.state.user === undefined) {
        return (
            <Modal show={true}>
                <Form>
                    <Modal.Header><Modal.Title>Login required</Modal.Title></Modal.Header>
                    <Modal.Body>
                          {this.state.loginError && (
                              <Alert bsStyle="danger">
                                <h3>Oh snap!</h3>
                                <p>{this.state.loginError.message}</p>
                              </Alert>
                          )}
                          <FieldGroup
                              id="username"
                              label="Username"
                              type="text"
                              value={this.state.username}
                              onChange={e => this.setState({username: e.target.value})}
                              placeholder="Username" />
                          <FieldGroup
                              id="password"
                              label="Password"
                              type="password"
                              value={this.state.password}
                              onChange={e => this.setState({password: e.target.value})}
                              placeholder="Password" />
                    </Modal.Body>
                    <Modal.Footer>
                        <Button bsStyle="primary" type="submit" onClick={e => {
                          e.preventDefault();
                          fetch(BASE_API_URL + '/login', {
                              method: 'post',
                              headers: {
                                  'Content-Type': 'application/json',
                                  'Accept': 'application/json'
                              },
                              body: JSON.stringify({
                                  username: this.state.username,
                                  password: this.state.password
                              })
                          }).then(checkStatus)
                          .then(parseJSON)
                          .then(data => {
                              this.setState({
                                  user: {token: data.token, id: data.id, username: this.state.username},
                                  username: undefined, password: undefined,
                                  loginError: undefined,
                              });
                              setCookie('user', JSON.stringify({token: data.token, id: data.id, username: this.state.username}), 10);
                              this.loadGrid();
                          })
                          .catch(error => this.setState({loginError: error}));
                        }}>Sign in</Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        )
    }

    let layout = this.state.widgets;
    let mobLayout = this.mobileLayout(layout);
    let alerts = [];
    if(this.state.gridSaved) {
        alerts.push(<Alert bsStyle="success">Layout saved</Alert>);
        setTimeout(() => this.setState({gridSaved: null}), 5 * 1000)
    }
    if(this.state.gridSaveError) {
        alerts.push(<Alert bsStyle="danger">Layout not saved !! {this.state.gridSaveError.message}</Alert>);
        setTimeout(() => this.setState({gridSaveError: null}), 5 * 1000)
    }
    if(this.state.widgetsError) {
        alerts.push(<Alert bsStyle="danger">Error loading widgets: {this.state.widgetsError.message}</Alert>);
        setTimeout(() => this.setState({widgetsError: null}), 5 * 1000)
    }
    return (
        <div className="container">
          {alerts.map((a, i) => <div key={i}>{a}</div>)}
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
            <Button bsStyle="primary" onClick={this.loadGrid}>Reload Grid</Button>
            <Button bsStyle="primary" onClick={() => {
                fetch(BASE_API_URL + '/logout', {
                    method: 'get',
                    headers: {
                        'Authorization': 'Bearer ' + this.state.user.token
                    }
                }).then(checkStatus)
                .then(() => {
                    this.setState({user: undefined});
                    setCookie("user", null, 10);
                })
                .catch(console.error);
            }}>Logout</Button>
          </ButtonToolbar>

          <NewWidgetModal
              show={this.state.showAddWidget}
              user_id={this.state.user.id}
              onHide={dirty => {
                  dirty && this.loadGrid();
                  this.setState({showAddWidget: false});
              }}
              auth_token={this.state.user.token}/>
          <UpdateWidgetModal
              show={this.state.showUpdateWidget}
              widget={this.state.widget}
              user_id={this.state.user.id}
              onHide={dirty => {
                  dirty && this.loadGrid();
                  this.setState({showUpdateWidget: false, widget: undefined});
              }}
              auth_token={this.state.user.token}/>
        </div>
    );
  }
}

export default Widgets;
