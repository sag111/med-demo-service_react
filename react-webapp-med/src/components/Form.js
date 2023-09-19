import React from "react";
{/*action = "http://0.0.0.0:5000" method="POST"*/}
class Form extends React.Component{
  render(){
    return(
      <form onSubmit={this.props.TransformText}>
        <textarea type="text" name="keyword" placeholder="Введите текст отзыва" cols="80" rows="8" charswidth="100"/>
        <div class="button_group">
            <button disabled={this.props.isSubmitButtonDisabled}>Разобрать</button>
            <button disabled={this.props.isSubmitButtonDisabled} type="button" onClick={this.props.DisplayFileExample}>Отобразить пример</button>
            <button disabled={this.props.isSubmitButtonDisabled} type="button" onClick={this.props.DisplayServiceExample}>Запросить пример</button>
        </div>
      </form>
    );
  }
}

export default Form;
