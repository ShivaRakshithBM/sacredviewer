import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import pprint
import json
# import glob #Recursive function not available in Python 3.4
import os
import time


from tornado.options import define, options

define("port", default=3333, help="run on the given port", type=int)
define("rootdir", default=".", help="root directory of the experiments stored by sacred", type=str)


def get_experiment_details(experiment_path):
    run = json.loads(open(experiment_path+"/run.json","r").read())
    cout = open(experiment_path+"/cout.txt").read()
    config = json.loads(open(experiment_path+"/config.json","r").read())
    return [cout,run,config]


def generate_formatted_row(k,v):
    return "<tr> <td style='border-top:0px'> <label style='font-weight:bold;margin-right:200px'>"+str(k)+"</label> </td>  <td style='border-top:0px'> "+str(v)+"</td> </tr>" 

def get_formatted_expt_details(experiment_path):
    [cout,run,config] = get_experiment_details(experiment_path)

    expt_details_rows =[generate_formatted_row("Experiment Directory",run['experiment']['base_dir']), 
                        generate_formatted_row("Main File",run['experiment']['mainfile']),
                        "<tr height:20px><td style='border:0px;background-color:#FFFFFF'></tr>"]

    expt_details_rows += [generate_formatted_row(k,v)  for k,v in config.items()]

    expt_details = """
    <table style='margin-left:auto;margin-right:auto'>
    """+" ".join(expt_details_rows) +"""
    </table>
    """ 

    expt_output = cout
    expt_files = generate_formatted_row("Sources",run['experiment']['sources'])
    expt_system = ""
    output = """
<div class="details_tabs">
  <input class = "tab_input" id="tab1" type="radio" name="tabs" checked>
  <label class ="tab_label" for="tab1">Experiment Details</label>
    
  <input class = "tab_input" id="tab2" type="radio" name="tabs">
  <label class ="tab_label" for="tab2">Output</label>
    
  <input class = "tab_input" id="tab3" type="radio" name="tabs">
  <label class ="tab_label" for="tab3">Files</label>
    
  <input class = "tab_input" id="tab4" type="radio" name="tabs">
  <label class ="tab_label" for="tab4">System Details</label>
    

  <div class="tab_content" id="content1">
    """+expt_details+"""
  </div>
    
  <div class="tab_content" id="content2" style="overflow:auto;max-height:500px;height:500px">
    """+expt_output+"""
  </div>
    
  <div class="tab_content" id="content3">
  """+expt_files+"""
  </div>


  <div class="tab_content" id="content4">
  """+expt_system+"""
  </div>

</div>
    """

    return output
def format_datetime(date_str):
  datetime_object = time.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
  return time.strftime("%d/%m/%y %H:%M:%S",datetime_object)

def find_experiments(root_folder):
    '''
    Find experiments in the given folder by recursively traversing all subdirectories from 
    root dir searching for config.json and identifies them as experiment folders.
    '''
    data = []
    # for configpath in glob.iglob('./**/config.json', recursive=True):
    for root, subFolders, files in os.walk(root_folder):
        if "config.json" in files:
            # configpath = os.path.join(root, '')
            expt_folder = root
            run = json.loads(open(expt_folder+"/run.json","r").read())
            config = json.loads(open(expt_folder+"/config.json","r").read())

            expt_description = config['desc_'] if "desc_" in config else ""
            data+=[[expt_folder,run['experiment']['name'],
                        expt_description,format_datetime(run['start_time']),format_datetime(run['heartbeat']),
                        # run['host']['hostname'],
                        run['status']] ]
    return data

class DataHandler(tornado.web.RequestHandler):
    def get(self):
        print("Get called!")
        dat = {"data":find_experiments(options.rootdir)}
        data_expt = json.dumps(dat)
        self.write(data_expt)


    def post(self):
        print("Post called!")
        data = self.request.body.decode('utf-8')
        experiment_folder = data.replace("%2F","/").split('=')[-1]
        self.write(get_formatted_expt_details(experiment_folder))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template.html", title="Viewing Experiments in "+options.rootdir)


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/data", DataHandler),
        (r"/details", DataHandler),
        (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": "./js"},),
        (r"/style/(.*)",tornado.web.StaticFileHandler, {"path": "./style"},),

    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()