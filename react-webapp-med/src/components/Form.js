import React from "react";
{/*action = "http://0.0.0.0:5000" method="POST"*/}
class Form extends React.Component{
  render(){
    return(
      <form onSubmit={this.props.TransformText}>
        <textarea type="text" name="keyword" placeholder="Введите текст отзыва" cols="80" rows="8" charswidth="100"/>
        <button>Разобрать</button>
      </form>
    );
  }
}

export default Form;
