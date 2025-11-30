import plotly
import plotly.graph_objects as go
import numpy as np

Az = np.load('Az.npy')
data=[go.Surface(z=Az[0], showscale=False, colorscale='viridis')]


frames = [dict(data= [dict(type='surface',
                           z=Az[k], 
                           showscale=False, 
                           colorscale='viridis'
                           )
                      ], 
               traces= [0],
               name='frame{}'.format(k)) for k  in  range(Az.shape[0])
         ]

sliders = [dict(steps= [dict(method= 'animate',
                             args= [['frame{}'.format(k) ],
                                     dict(mode= 'immediate',
                                          frame= dict(duration=50, redraw= True ),
                                          transition=dict( duration= 0)
                                         )
                                   ],
                             label='{:.2f}'.format(k)) for k in range(Az.shape[0])
                       ], 
                transition= dict(duration= 1 ),
                x=0,
                y=0, 
                currentvalue=dict(font=dict(size=12), 
                                  prefix='Iteration: ', 
                                  visible=True, 
                                  xanchor= 'center'),  
                len=1.0
               )
          ]

layout = dict(template='simple_white',
              title='Surface relaxation',
              # autosize=False,
              # width=600,
              # height=600,
              showlegend=False,
              scene=dict(
                         xaxis = go.layout.scene.XAxis(showspikes=False),
                         yaxis = go.layout.scene.YAxis(showspikes=False),
                         zaxis = go.layout.scene.ZAxis(showspikes=False),
              aspectratio=dict(x=1, y=1, z=1)),
              updatemenus=[dict(type='buttons', showactive=False,
                                y=0,
                                x=1.15,
                                xanchor='right',
                                yanchor='top',
                                pad=dict(t=0, r=10),
                                buttons=[dict(label='Play',
                                              method='animate',
                                              args=[None, 
                                                    dict(frame=dict(duration=500, 
                                                                    redraw=True),
                                                         transition=dict(duration=0),
                                                         fromcurrent=True,
                                                         mode='immediate'
                                                        )
                                                   ]
                                             )
                                        ]
                               )
                          ],
              sliders=sliders
             )

fig = go.Figure(data=data, layout=layout, frames=frames)
plotly.offline.plot(fig, filename='Surface_relaxation.html', auto_open=False)