<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9AMAP</title>
<style>
body {
  background-color: #ffcc00;
  text-align: center;
  font-family: sans-serif;
  padding: 10px;
}
textarea {
  background-color: #ffffff;
  border: 2px solid #333333;
  padding: 0px;
  width: 100%;
  margin-bottom: 0px;
}
</style>
</head>
<body>
<p>START . END . DEP | ARR HHMM</p>
<form action="/query" method="POST">
 <textarea name="q" placeholder="" rows="3"></textarea>
  <br>
  <br>
  <input type="submit" value="Submit">
</form>
<p><a href="/admin">admin</a></p>
</body>
</html>
