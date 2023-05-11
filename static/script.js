"use strict";

window.addEventListener("load", function () {
  document.getElementById("sign-out").onclick = function () {
    // ask firebase to sign out the user
    firebase.auth().signOut();
  };

  var uiConfig = {
    signInSuccessUrl: "/",
    signInOptions: [firebase.auth.EmailAuthProvider.PROVIDER_ID],
  };

  function setBodyClassVisibility(user) {
    if (user) {
      document.getElementById("sign-out").hidden = false;
      document.getElementById("login-info").hidden = false;
      document.getElementById("enterSharing").hidden = false;
      document.body.classList.remove("logged-out");
      document.body.classList.add("logged-in");
      console.log(`Signed in as ${user.displayName} (${user.email})`);
      user.getIdToken().then(function (token) {
        document.cookie = "token=" + token;
      });
    } else {
      document.getElementById("sign-out").hidden = true;
      document.getElementById("login-info").hidden = true;
      document.getElementById("enterSharing").hidden = true;
      document.body.classList.remove("logged-in");
      document.body.classList.add("logged-out");
      var ui = new firebaseui.auth.AuthUI(firebase.auth());
      ui.start("#firebase-auth-container", uiConfig);
      document.cookie = "token=";
    }
  }

  firebase.auth().onAuthStateChanged(setBodyClassVisibility, function (error) {
    console.log(error);
    alert("Unable to log in: " + error);
  });
});
