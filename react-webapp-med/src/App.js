import React, { Component } from "react";
import { useState, useEffect } from 'react';
import "./App.css";

import Form from "./components/Form";

var res_fetch;

const transformFunction = (input) => {
    var fileJson = require('./test.json');
    var randIndex = Math.floor(Math.random() * fileJson.length);

    return fetch('/', {
       method: 'POST',
       body: input,
     }).then((response) => response.json())
        .then( (data) =>  {res_fetch = data.data});
}

const splitOnce = (s, on) => {
  var [first, ...rest] = s.split(on);
  return [first, rest.length > 0 ? rest.join(on) : null];
}

const prepareColor = (medEntityType) => {
  if (medEntityType === 'Medication') {
    return 'green';
  }
  if (medEntityType === 'Disease') {
    return 'red';
  }
  if (medEntityType === 'ADR') {
    return 'blue';
  }
  if (medEntityType === 'Note') {
    return 'yellow';
  }
}

const checkOnlyOnce = (str, list) => {
    var i;
    for (i = 0; i < list.length; i++) {
      if (list[i].text.toLowerCase() === str.toLowerCase()) {
          return i;
      }
    }
}

const prepareInBrackets = (obj, str) => {
  if (obj.ATC) {
    return str.toLowerCase() + ` (${obj.ATC})`;
  }
  if (obj.MedDRA) {
    return str.toLowerCase() + ` (${obj.MedDRA})`;
  }
  if (obj.MKB10) {
    return str.toLowerCase() + ` (${obj.MKB10})`;
  }
  if (obj.source_group) {
    return str.toLowerCase() + ` (${obj.source_group})`;
  }
  if (obj.Medfrom_standart) {
    return str.toLowerCase() + ` (${obj.Medfrom_standart})`;
  }
  if (obj.MedMaker) {
    return str.toLowerCase() + ` (${obj.MedMaker})`;
  }
  if (obj.MedFrom) {
    return str.toLowerCase() + ` (${obj.MedFrom})`;
  }
  return str.toLowerCase();
}

class App extends Component {

  state = {
    found: false,
    title: "",
    text: "",
    url: "",
    entities: [],
    tableData: {},
    error: undefined
  }

  gettingData = async (e) => {
    e.preventDefault();
    var input = e.target.elements.keyword.value;
    if (input){
      transformFunction(input).then(() => {
        var reviewExample = res_fetch;
        const entities = Object.values(reviewExample.entities);
        var text = reviewExample.text;
        var totalArr = [];
        var totalObj = {};
        var totalobj = {};
        totalObj.Medication = {};
        totalObj.Disease = {};

        const total = entities.map((obj) => {
          const markupColor = prepareColor(obj.MedEntityType);
          obj.spans.forEach(span => {
            const substr = reviewExample.text.substring(span.begin, span.end);
            if (text) {
              if (text.includes(substr)) {
                const dataArr = splitOnce(text, substr);
                if (obj.MedEntityType === "Medication") {
                  totalArr.push(dataArr[0] + `<span class="text_${markupColor}" data-title=${obj.MedType}>`+substr+'</span>');
                } else if (obj.MedEntityType === "Disease") {
                  totalArr.push(dataArr[0] + `<span class="text_${markupColor}" data-title=${obj.DisType}>`+substr+'</span>');
                } else {
                  totalArr.push(dataArr[0] + `<span class="text_${markupColor}">`+substr+'</span>');
                }
                text = dataArr[1];
              }
            }
          });
          obj.Context.map(context => {
            if (!totalobj[context]) {
              totalobj[context] = []
            }
            if (!totalobj[context][obj.MedEntityType]) {
              totalobj[context][obj.MedEntityType] = []
            }
            if (obj.MedEntityType === "Medication") {
              var typePlusEntitie = obj.MedType + ': '  + prepareInBrackets(obj, `${obj.text}`);
            }
            if (obj.MedEntityType === "Disease") {
              var typePlusEntitie = obj.DisType + ': '  + prepareInBrackets(obj, `${obj.text}`);
            }
            if (obj.MedEntityType === "ADR" || obj.MedEntityType === "Note") {
              var typePlusEntitie = prepareInBrackets(obj, `${obj.text}`);
            }
            if (!totalobj[context][obj.MedEntityType].includes(typePlusEntitie)) {
              totalobj[context][obj.MedEntityType].push(typePlusEntitie);
            }

          });



          if (obj.MedEntityType === "Medication") {
            obj.Context.map(context => {
              if (!totalObj.Medication[context]) {
                totalObj.Medication[context] = [];
              }
              const typePlusEntitie = obj.MedType + ': '  + prepareInBrackets(obj, `${obj.text}`);
              if (!totalObj.Medication[context].includes(typePlusEntitie)) {
                totalObj.Medication[context].push(typePlusEntitie);
              }
            })
          }

          if (obj.MedEntityType === "Disease") {
            obj.Context.map(context => {
              if (!totalObj.Disease[context]) {
                totalObj.Disease[context] = [];
              }
              const typePlusEntitie = obj.DisType + ': '  + prepareInBrackets(obj, `${obj.text}`);
              if (!totalObj.Disease[context].includes(typePlusEntitie)) {
                totalObj.Disease[context].push(typePlusEntitie);
              }
            })
          }
        });

        const result = totalArr.join('');
        const resultSplit = result.split('\n', 5);

        this.setState({
          found: true,
          title: resultSplit[2],
          text: resultSplit[4],
          url: resultSplit[0],
          entities: entities,
          tableData: totalobj,
          error: undefined
        });


      });

    } else {
      this.setState({
        found: false,
        title: "",
        text: "",
        url: "",
        entities: [],
        tableData: {},
        error: "Введите текст отзыва"
      });
    }


  }

  render() {
    return(
      <div className="wrapper">
        <div className="flex-container">
          <h1> Med-demo </h1>
          <Form TransformText={this.gettingData}/>
          <div>
            { this.state.found &&
              <div>

                <div className="reviewtext">
                  <p>
                    <b dangerouslySetInnerHTML={{ __html: this.state.title }}/>
                  </p>
                  <div dangerouslySetInnerHTML={{ __html: this.state.text }}/>
                  <p> <a href={this.state.url}> {this.state.url} </a> </p>
                </div>
              </div>
            }
            <p> {this.state.error} </p>
          </div>

          { this.state.found &&
            <div >
              <table align="center">
                <thead>
                  <tr>
                    <th>Medication</th>
                    <th>Disease</th>
                    <th>ADR</th>
                    <th>Note</th>
                  </tr>
                </thead>
                <tbody>
                {
                  Object.entries(this.state.tableData).map(([key, value]) => (
                    <tr>
                      <td>
                        {value.Medication ?
                          Object.entries(value.Medication).map(([k,v]) => (
                              <p>{v}</p>
                          ))
                          :
                          <></>
                        }
                      </td>
                      <td>
                        {value.Disease ?
                          Object.entries(value.Disease).map(([k,v]) => (
                              <p>{v}</p>
                          ))
                          :
                          <></>
                        }
                      </td>
                      <td>
                        {value.ADR ?
                          Object.entries(value.ADR).map(([k,v]) => (
                              <p>{v}</p>
                          ))
                          :
                          <></>
                        }
                      </td>
                      <td>
                        {value.Note ?
                          Object.entries(value.Note).map(([k,v]) => (
                              <p>{v}</p>
                          ))
                          :
                          <></>
                        }
                      </td>
                    </tr>
                  ))
                }
                </tbody>
              </table>
            </div>
          }

        </div>
      </div>
    );
  }
}

export default App;
