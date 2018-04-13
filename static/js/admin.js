'use strict'

document.getElementById('mlh-trust-badge').outerHTML = ''

let pn = new PubNub({
  publishKey: '',
  subscribeKey: '',
  ssl: true
})

pn.subscribe({
  channels: ['hacktcnj17-admin']
})

pn.addListener({
  message: (msg) => {
    msg = msg.message
    console.log(msg)
    const id = msg.id
    if (msg.action === 'check_in') {
      document.getElementById(id + '-check_in').outerHTML = ''
      document.getElementById(id + '-checked_in').innerHTML = 'True'
    } else if (msg.action === 'drop') {
      document.getElementById(id + '-row').outerHTML = ''
    } else if (msg.action === 'promote_from_waitlist') {
      document.getElementById(id + '-promote_from_waitlist').outerHTML = ''
      document.getElementById(id + '-waitlisted').innerHTML = 'False'
    } else if (msg.action === 'new_user' || msg.action === 'refresh' || msg.action.split(':')[0] === 'change_admin') {
      window.location.reload(true)
    }
  }
})

let successColor = '#18BC9C'
let errColor = '#E74C3C'

$(document).ready(() => {
  let timeout = setTimeout("window.location.reload(true);", 300000)

  const resetTimeout = () => {
    clearTimeout(timeout)
    timeout = setTimeout("window.location.reload(true);", 300000)
  }

  $('a.check_in').click((e) => {
    e.preventDefault()
    let id = e.target.id.split('-')[0]
    console.log('check in ' + id)
    checkIn(id)
  })
  $('a.drop').click((e) => {
    e.preventDefault()
    let id = e.target.id.split('-')[0]
    console.log('drop ' + id)
    drop(id)
  })
  $('a.demote_admin').click((e) => {
    e.preventDefault()
    let id = e.target.id.split('-')[0]
    console.log('demote admin ' + id)
    changeAdmin(id, 'demote')
  })
  $('a.promote_admin').click((e) => {
    e.preventDefault()
    let id = e.target.id.split('-')[0]
    console.log('promote admin ' + id)
    changeAdmin(id, 'promote')
  })
  $('a.promote_from_waitlist').click((e) => {
    e.preventDefault()
    let id = e.target.id.split('-')[0]
    console.log('promote waitlist ' + id)
    promoteFromWaitlist(id)
  })
})

const promoteFromWaitlist = (id) => {
  swal({
    title: 'Promote hacker ' + id + ' off the waitlist?',
    text: 'Are you sure you wish to promote this hacker off the waitlist?',
    icon: 'info',
    buttons: {
      cancel: {
      	text: 'Cancel',
        value: null,
        visible: true,
        className: '',
        closeModal: true
      },
      confirm: {
        text: 'Yes, promote!',
        value: true,
        visible: true,
        className: '',
        closeModal: false
      }
    },
    className: 'swal-success'
  }, () => {
    $.get('/promote_from_waitlist?mlh_id=' + id, (data) => {
      let title = ''
      let msg = ''
      let icon = ''
      if (data.status === 'success') {
        title = 'Promoted!'
        msg = 'The hacker was successfully promoted off the waitlist!'
        icon = 'success'
      } else {
        title = 'Error!'
        msg = JSON.stringify(data)
        icon = 'error'
      }
      swal(title, msg, icon)
    })
  })
}

const changeAdmin = (id, action) => {
  swal({
    title: 'Modify:' + action + ' admin prviliges on hacker ' + id + ' ?',
    text: 'Are you sure you wish to modify:' + action + ' this hacker\'s administrative privileges?',
    icon: 'warning',
    buttons: {
      cancel: {
      	text: 'Cancel',
        value: null,
        visible: true,
        className: '',
        closeModal: true
      },
      confirm: {
        text: 'Yes, ' + action + '!',
        value: true,
        visible: true,
        className: '',
        closeModal: false
      }
    },
    className: 'swal-error'
  }, () => {
    $.get('/change_admin?mlh_id=' + id + '&action=' + action, (data) => {
      let title = ''
      let msg = ''
      let icon = ''
      if (data.status === 'success') {
        title = 'Modified!'
        msg = 'The hacker\'s administrative privileges have been modified:' + action + '!'
        icon = 'success'
      } else {
        title = 'Error!'
        msg = JSON.stringify(data)
        icon = 'error'
      }
      swal({title: title, msg: msg, icon: icon}, () => window.location.reload(true))
    })
  })
}

const drop = (id) => {
  swal({
    title: 'Drop hacker ' + id + ' ?',
    text: 'Are you sure you wish to drop this hacker\'s application?',
    icon: 'warning',
    buttons: {
      cancel: {
      	text: 'Cancel',
        value: null,
        visible: true,
        className: '',
        closeModal: true
      },
      confirm: {
        text: 'Yes, drop!',
        value: true,
        visible: true,
        className: '',
        closeModal: false
      }
    },
    className: 'swal-error'
  }, () => {
    $.get('/drop?mlh_id=' + id, (data) => {
      let title = ''
      let msg = ''
      let icon = ''
      if (data.status === 'success') {
        title = 'Dropped!'
        msg = 'The hacker\'s application was successfully dropped!'
        icon = 'success'
      } else {
        title = 'Error!'
        msg = JSON.stringify(data)
        icon = 'error'
      }
      swal(title, msg, icon)
    })
  })
}

const checkIn = (id) => {
  swal({
    title: 'Check in hacker ' + id + ' ?',
    text: 'Are you sure you wish to check in this hacker?',
    icon: 'info',
    buttons: {
      cancel: {
      	text: 'Cancel',
        value: null,
        visible: true,
        className: '',
        closeModal: true
      },
      confirm: {
        text: 'Yes, check in!',
        value: true,
        visible: true,
        className: '',
        closeModal: false
      }
    },
    className: 'swal-success'
  }, () => {
    $.get('/check_in?mlh_id=' + id, (data) => {
      let title = ''
      let msg = ''
      let icon = ''
      if (data.status === 'success') {
        title = 'Checked in!'
        msg = 'The hacker was checked in!'
        icon = 'success'
      } else {
        title = 'Error!'
        msg = JSON.stringify(data)
        icon = 'error'
      }

      if (data.status === 'success' && data.action === 'check_in' && data.minor === true) {
        msg += '\nATTENTION:\nHacker is a minor, please ensure they have the minor consent form!'
      }

      swal(title, msg, icon)
    })
  })
}
