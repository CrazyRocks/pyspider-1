$(document).ready(function(){

   var selected_column = '';
//  保存脚本
  $('#save-task-btn').on('click', function() {
        save_script("保存成功")
   });


//  保存脚本
   $('.list-column-item').on('click', function() {
      selected_column = $(this).text();
      $("#select-column-btn").text(selected_column);
   });

//   打开脚本界面
    $('#open-script-btn').on('click', function() {
       scriptUrl = location.pathname+'/debug';
       window.open(scriptUrl);
   });


//   添加抽取字段
   $('#add-column-btn').on('click', function() {
        if(selected_column) {
            var inspired_word = $("input[name=inspired-word]").val();
            var column_name = selected_column;
            var extract_content = $("input[name=extract-content]").val();

            $.ajax({
              type: "POST",
              url: location.pathname+'/add',
              data: {
                inspiredWord: inspired_word,
                columnName: column_name,
                extractContent: extract_content
              },
              success: function(data) {
                if(inspired_word.trim() === "" || extract_content.trim() === "") {
                    alert("删除成功");
                } else {
                    alert("添加成功");
                }
              },
              error: function(xhr, textStatus, errorThrown) {
                alert("save error!\n"+xhr.responseText);
              }
            });
         } else {
            alert('请选择字段名称');

         }

    });
});


//保存脚本到后台txt文件对应的函数
var save_script = function(alert_s){
    var begin_url = $("input[name=begin-url]").val();
    var detail_page_url = $("input[name=detail-page-url]").val();
    var next_page_url = $("input[name=next-page-url]").val();
    var save_path = $("input[name=save-path]").val();
    var content_mark = $("input[name=content-mark]").val();
    $.ajax({
      type: "POST",
      url: location.pathname+'/save',
      data: {
        beginUrl: begin_url,
        detailPageUrl: detail_page_url,
        nextPageUrl: next_page_url,
        savePath: save_path,
        contentMark: content_mark
      },
      success: function(data) {
        alert(alert_s);
      },
      error: function(xhr, textStatus, errorThrown) {
        alert("save error!\n"+xhr.responseText);
      }
    });
};