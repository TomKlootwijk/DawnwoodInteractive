package nl.dawnwood.kernel;

import android.app.Activity;
import android.app.ActivityManager;
import android.os.Build;
import android.os.Bundle;
import android.os.PowerManager;
import android.os.SystemClock;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    static { System.loadLibrary("dawnwood_jni"); }
    private static native String nativeRun(String[] args);
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final List<Button> buttons = new ArrayList<>();
    private TextView output;
    private boolean busy;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL);
        int p=(int)(16*getResources().getDisplayMetrics().density);layout.setPadding(p,p,p,p);
        TextView title=new TextView(this);title.setText("Dawnwood Interactive\nNumerical Vulkan kernel · DWI-N1 0.5");title.setTextSize(20);layout.addView(title);
        addButton(layout,"Probe Mali / Vulkan", "probe",1,0);
        addButton(layout,"CPU source-profile tests", "selftest",64,0);
        addButton(layout,"Compare CPU and GPU — every epoch", "verify",128,16);
        addButton(layout,"Run numerical circulation", "run",4096,64);
        output=new TextView(this);output.setTextIsSelectable(true);output.setText("Reports are saved under the app's files/reports directory. No network, root access, or graphics rendering is required.");
        ScrollView scroll=new ScrollView(this);scroll.addView(output);layout.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(layout);
        if(getIntent().getBooleanExtra("autorun",false)){
            String command=getIntent().getStringExtra("command");
            String runId=getIntent().getStringExtra("run_id");
            launch(command==null?"verify":command,getIntent().getIntExtra("count",128),getIntent().getIntExtra("steps",16),runId==null?"adb":runId,getIntent().getIntExtra("batch",8),getIntent().getFloatExtra("budget_fraction",0.8f));
        }
    }
    private void addButton(LinearLayout layout,String text,String command,int count,int steps){Button b=new Button(this);b.setText(text);b.setOnClickListener(v->launch(command,count,steps,"interactive_"+System.currentTimeMillis(),8,0.8f));buttons.add(b);layout.addView(b);}
    private JSONObject deviceContext() throws Exception {
        JSONObject d=new JSONObject();d.put("model",Build.MODEL);d.put("manufacturer",Build.MANUFACTURER);d.put("sdk",Build.VERSION.SDK_INT);d.put("abi",Build.SUPPORTED_ABIS[0]);
        ActivityManager.MemoryInfo info=new ActivityManager.MemoryInfo();((ActivityManager)getSystemService(ACTIVITY_SERVICE)).getMemoryInfo(info);d.put("system_total_ram_bytes",info.totalMem);d.put("system_available_ram_bytes",info.availMem);d.put("system_low_memory_threshold_bytes",info.threshold);d.put("system_low_memory",info.lowMemory);
        if(Build.VERSION.SDK_INT>=29)d.put("android_thermal_status",((PowerManager)getSystemService(POWER_SERVICE)).getCurrentThermalStatus());
        Intent battery=registerReceiver(null,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));if(battery!=null)d.put("battery_temperature_celsius",battery.getIntExtra(BatteryManager.EXTRA_TEMPERATURE,0)/10.0);
        return d;
    }
    private void launch(String command,int count,int steps,String runId,int batch,float budgetFraction){
        if(busy)return;
        if(!(command.equals("probe")||command.equals("selftest")||command.equals("verify")||command.equals("run"))){output.setText("Unknown command");return;}
        final String id=runId.replaceAll("[^A-Za-z0-9_-]","_");
        busy=true;for(Button b:buttons)b.setEnabled(false);output.setText("Running "+command+" on the device.\nRun ID: "+id);
        executor.execute(()->{
            String display;
            try{
                JSONObject report=new JSONObject();report.put("run_id",id);report.put("android_before",deviceContext());long start=SystemClock.elapsedRealtime();
                String[] args={command,"--count",Integer.toString(count),"--steps",Integer.toString(steps),"--batch",Integer.toString(batch),"--budget-fraction",Float.toString(budgetFraction)};
                report.put("native_arguments",new JSONArray(args));
                report.put("runtime",new JSONObject(nativeRun(args)));report.put("elapsed_wall_ms",SystemClock.elapsedRealtime()-start);report.put("android_after",deviceContext());report.put("finished",true);
                display=report.toString(2);File dir=new File(getFilesDir(),"reports");if(!dir.exists()&&!dir.mkdirs())throw new IllegalStateException("Cannot create report directory");
                File temp=new File(dir,id+".tmp"),target=new File(dir,id+".json");try(FileOutputStream f=new FileOutputStream(temp)){f.write(display.getBytes(StandardCharsets.UTF_8));f.getFD().sync();}if(!temp.renameTo(target))throw new IllegalStateException("Cannot commit report");
            }catch(Exception e){display="Run failed: "+e;}
            final String text=display;runOnUiThread(()->{output.setText(text);busy=false;for(Button b:buttons)b.setEnabled(true);});
        });
    }
    @Override public void onDestroy(){executor.shutdown();super.onDestroy();}
}
