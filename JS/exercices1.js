let sequence = [1,1,2,3,5,8,13];

for (let i = 0; i < sequence.length; i++)
{
    console.log(sequence[i])
}

const soustableau = sequence.map( e => e*2)

const soustableaupaire = sequence.filter(e => e%2)

const sometab = sequence.reduce((sum,e)=>sum+e)