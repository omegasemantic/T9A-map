<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9AMAP — admin</title>
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

<form action="/set_city" method="POST">
  <input type="text" name="city" value="{{city}}"><br>
  <br>
  <input type="submit" value="Set city">
</form>
<br>
<form action="/set_country" method="POST">
  <input type="text" name="country" value="{{country}}"><br>
  <br>
  <input type="submit" value="Set country">
</form>

<hr>

<p>Favs</p>
<table>
<tr><th>Name</th><th></th></tr>
%for name, value in favs:
<tr>
  <td>{{name}}</td>
  <td>
    <form action="/delete_fav" method="POST" style="display:inline">
      <input type="hidden" name="name" value="{{name}}">
      <input type="submit" value="delete">
    </form>
  </td>
</tr>
%end
</table>

<hr>

<p>Add fav</p>
<form action="/add_fav" method="POST">
  <input type="text" name="name" placeholder="name"><br>
  <br>
  <input type="text" name="value" placeholder="ChIJ.../lat,lng/address"><br>
  <br>
  <input type="submit" value="Add">
</form>

<p><a href="/ticket.html">switcher</a></p>
<p><a href="/">new query</a></p>

</body>
</html>
