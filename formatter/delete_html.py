import os

def delete_html(conversion_start,output_dir):
    i = 0
    for (path,dirs,files) in os.walk(output_dir):
        for basename in files:
            fullname = os.path.join(path,basename)
            if fullname.endswith(".html") and os.path.getmtime(fullname) < conversion_start:
                i += 1
                print "delete_html: %d. %s"%(i,basename)
                os.remove(fullname)
 
