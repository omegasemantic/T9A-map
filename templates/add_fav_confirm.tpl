<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9AMAP — confirm</title>
<style>
body {
  background-color: #ffcc00;
  text-align: center;
  font-family: sans-serif;
  padding: 10px;
}
</style>
</head>
<body>

<p>Add this fav?</p>
<p>{{name}} = {{value}}</p>

<form action="/add_fav_commit" method="POST">
  <input type="hidden" name="name" value="{{name}}">
  <input type="hidden" name="value" value="{{value}}">
  <input type="submit" value="Confirm">
</form>

<p><a href="/admin">cancel</a></p>

</body>
</html>
