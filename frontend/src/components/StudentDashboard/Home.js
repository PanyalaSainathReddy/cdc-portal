import React from 'react';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Table from '@material-ui/core/Table';
import instance from '../../api/axios';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Avatar from '@material-ui/core/Avatar';
import SchoolIcon from '@material-ui/icons/School';
import PhoneIcon from '@material-ui/icons/Phone';
import EmailIcon from '@material-ui/icons/Email';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';
import CancelIcon from '@material-ui/icons/Cancel';
import LinkIcon from '@material-ui/icons/Link';
import DeleteForeverIcon from '@material-ui/icons/DeleteForever';
import VisibilityIcon from '@material-ui/icons/Visibility';
import Chip from '@material-ui/core/Chip';

const useStyles = makeStyles((theme) => ({
  paper: {
    padding: theme.spacing(2),
    display: 'flex',
    overflow: 'auto',
    flexDirection: 'column',
    width: '100%',
    marginTop: '20px',
  },
  avatar: {
    width: theme.spacing(18),
    height: theme.spacing(18),
    margin: '10% auto 6% auto',
  },
}));

function getDate(date) {
  date = new Date(date);
  return date.toDateString();
}

function get_link(link) {
  try {
    link = new URL(link);
    link = link.pathname;
  } catch {}
  let backend = `http://${
    process.env.BACKEND_HOST ? process.env.BACKEND_HOST : '127.0.0.1'
  }:8000`;
  let ln = process.env.NODE_ENV === 'production' ? link : backend + link;
  return ln;
}

function Home() {
  const classes = useStyles();
  const [data, setdata] = React.useState('');
  const [resume, setresumeData] = React.useState([]);
  const [upcominginternoffers, setupcominginternoffers] = React.useState([]);
  const [upcomingjoboffers, setupcomingjoboffers] = React.useState([]);
  const [internoffers, setinternoffers] = React.useState([]);
  const [joboffers, setjoboffers] = React.useState([]);

  function deleteRow(event, index, id) {
    event.preventDefault();
    instance
      .delete('student/resume/' + id)
      .then((res) => {
        resume.splice(index, 1);
        setresumeData(resume);
        window.location.reload();
      })
      .catch((error) => {
        console.log(error);
        window.alert('failed to delete resume');
      });
  }
  React.useEffect(() => {
    instance
      .get('student/resumes/')
      .then((res) => {
        //console.log(res.data);
        let adt = {};
        try {
          // If no resume is present
          adt = res.data[0].student;
          setresumeData(res.data);
        } catch {
          adt = res.data;
        }
        adt.std_image = get_link(adt.std_image);
        adt.email = adt.user.email;
        adt.user = adt.user.first_name + ' ' + adt.user.last_name;
        adt.program_branch = adt.program_branch.name;
        setdata(adt);
      })
      .catch(function (error) {
        if (error.response) {
          console.log(error.response);
          if (error.response.status === 403) {
            window.alert('Complete Your Profile');
            window.location = '/student-register';
          }
        }
      });
    instance.get('student/applied_offers/').then((res) => {
      console.log(res.data);
      let dat = [];
      res.data.Internships.forEach((element) => {
        element.name = element.profile.company.name;
        element.designation = element.profile.designation;
        element.adv = element.profile.id;
        dat.push(element);
        console.log(element);
      });
      setinternoffers(dat);
      dat = [];
      res.data.Jobs.forEach((element) => {
        element.name = element.profile.company.name;
        element.designation = element.profile.designation;
        element.adv = element.profile.id;
        dat.push(element);
      });
      setjoboffers(dat);
    });
    instance
      .get('student/upcoming_offers/')
      .then((res) => {
        console.log(res.data);
        let dat = [];
        try {
          res.data.Internships.forEach((element) => {
            element.name = element.company.name;
            element.type = 'Intern';
            dat.push(element);
          });
          setupcominginternoffers(dat);
        } catch (e) {}
        dat = [];
        res.data.Jobs.forEach((element) => {
          element.name = element.company.name;
          element.type = 'Job';
          dat.push(element);
        });
        setupcomingjoboffers(dat);
      })
      .catch(function (error) {
        if (error.response) {
          console.log(error.response);
          if (error.response.status === 403) {
            window.alert(error.response.data['Error']);
          }
        }
      });
  }, []);
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={8}>
        {internoffers.length === 0 ? (
          <div />
        ) : (
          <Paper className={classes.paper}>
            <React.Fragment>
              <Typography
                component="h2"
                variant="h6"
                color="primary"
                gutterBottom
              >
                Applied Internships Offers
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>View</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Designation</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {internoffers.map((row, index) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <VisibilityIcon
                          style={{
                            marginLeft: '10%',
                            paddingTop: '1%',
                            cursor: 'pointer',
                          }}
                          onClick={() => {
                            window.location =
                              '/student-dashboard/advertisement/' + row.adv;
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        {getDate(row.application_timestamp)}
                      </TableCell>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.designation}</TableCell>
                      <TableCell>
                        {row.is_accepted ? (
                          <Chip color="green" label="Accepted" />
                        ) : (
                          <Chip label="Applied" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </React.Fragment>
          </Paper>
        )}
        {joboffers.length === 0 ? (
          <div />
        ) : (
          <Paper className={classes.paper}>
            <React.Fragment>
              <Typography
                component="h2"
                variant="h6"
                color="primary"
                gutterBottom
              >
                Applied Job Offers
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>View</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Designation</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {joboffers.map((row, index) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <VisibilityIcon
                          style={{
                            marginLeft: '10%',
                            paddingTop: '1%',
                            cursor: 'pointer',
                          }}
                          onClick={() => {
                            window.location =
                              '/student-dashboard/advertisement/' + row.adv;
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        {getDate(row.application_timestamp)}
                      </TableCell>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.designation}</TableCell>
                      <TableCell>
                        {row.is_accepted ? (
                          <Chip color="green" label="Accepted" />
                        ) : (
                          <Chip label="Applied" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </React.Fragment>
          </Paper>
        )}
        <Paper className={classes.paper}>
          <React.Fragment>
            <Typography
              component="h2"
              variant="h6"
              color="primary"
              gutterBottom
            >
              Resume Updates
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>S No.</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Refrence Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {resume.map((row, index) => (
                  <TableRow key={row.id}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>{getDate(row.timestamp)}</TableCell>
                    <TableCell>
                      <a
                        href={get_link(row.file)}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          color: 'inherit',
                          textDecoration: 'none',
                        }}
                      >
                        {row.reference}
                      </a>
                    </TableCell>
                    <TableCell>
                      {row.is_verified ? (
                        <CheckCircleIcon style={{ color: 'green' }} />
                      ) : (
                        <CancelIcon color="error" />
                      )}
                    </TableCell>
                    <TableCell>
                      <a
                        href={get_link(row.file)}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          color: 'inherit',
                          textDecoration: 'none',
                          marginRight: '10px',
                        }}
                      >
                        <LinkIcon />
                      </a>
                      {!row.is_verified ? (
                        <a
                          href="/"
                          onClick={(event) => {
                            deleteRow(event, index, row.id);
                          }}
                          style={{ color: 'inherit', textDecoration: 'none' }}
                        >
                          <DeleteForeverIcon color="error" />
                        </a>
                      ) : (
                        <div />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </React.Fragment>
        </Paper>
        {upcominginternoffers.length === 0 ? (
          <div />
        ) : (
          <Paper className={classes.paper}>
            <React.Fragment>
              <Typography
                component="h2"
                variant="h6"
                color="primary"
                gutterBottom
              >
                Upcoming Internships Offers
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>S No.</TableCell>
                    <TableCell>View</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Designation</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {upcominginternoffers.map((row, index) => (
                    <TableRow key={row.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                        <VisibilityIcon
                          style={{
                            marginLeft: '10%',
                            paddingTop: '1%',
                            cursor: 'pointer',
                          }}
                          onClick={() => {
                            window.location =
                              '/student-dashboard/advertisement/' + row.adv;
                          }}
                        />
                      </TableCell>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.designation}</TableCell>
                      <TableCell>
                        {row.active ? (
                          <Chip color="green" label="Active" />
                        ) : (
                          <Chip label="Upcoming" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </React.Fragment>
          </Paper>
        )}
        {upcomingjoboffers.length === 0 ? (
          <div />
        ) : (
          <Paper className={classes.paper}>
            <React.Fragment>
              <Typography
                component="h2"
                variant="h6"
                color="primary"
                gutterBottom
              >
                Upcoming Job Offers
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>S No.</TableCell>
                    <TableCell>View</TableCell>
                    <TableCell>Company</TableCell>
                    <TableCell>Designation</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {upcomingjoboffers.map((row, index) => (
                    <TableRow key={row.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                        <VisibilityIcon
                          style={{
                            marginLeft: '10%',
                            paddingTop: '1%',
                            cursor: 'pointer',
                          }}
                          onClick={() => {
                            window.location =
                              '/student-dashboard/advertisement/' + row.adv;
                          }}
                        />
                      </TableCell>
                      <TableCell>{row.name}</TableCell>
                      <TableCell>{row.designation}</TableCell>
                      <TableCell>
                        {row.active ? (
                          <Chip color="green" label="Active" />
                        ) : (
                          <Chip label="Upcoming" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </React.Fragment>
          </Paper>
        )}
      </Grid>
      <Grid item xs={12} sm={4}>
        <Paper className={classes.paper}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Student
          </Typography>
          <Avatar
            alt="Profile Image"
            src={data.std_image}
            className={classes.avatar}
          />
          <Typography variant="subtitle1" align="center" gutterBottom>
            {data.user} ({data.roll_no})
          </Typography>
          <ListItem>
            <ListItemIcon>
              <SchoolIcon />
            </ListItemIcon>
            <ListItemText primary={data.program_branch} />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <PhoneIcon />
            </ListItemIcon>
            <ListItemText primary={data.phone} />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <EmailIcon />
            </ListItemIcon>
            <ListItemText primary={data.email} />
          </ListItem>
        </Paper>
        <Paper className={classes.paper} style={{ marginTop: '10px' }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            Announcements
          </Typography>
        </Paper>
      </Grid>
    </Grid>
  );
}

export default Home;
