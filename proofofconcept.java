public class challenge {

	public static void main(String[] args) {

		
		
		
		// Because I dont know how to do parsing shit
		System.out.println("Summoner 1");
		String summoner1 = TextIO.getlnString(); 
		System.out.println("Summoner 2");
		String summoner2 = TextIO.getlnString();
		// Because I don't know how to work with API
		System.out.println("Champion 1 Mastery Point");
		double champion1_masteryPoint = TextIO.getlnDouble();
		System.out.println("Champion 1 Mastery Level");
		double champion1_masteryLevel = TextIO.getlnDouble();
		System.out.println("Number of Games played on champion 1");
		double champion1_gamesPlayed = TextIO.getlnDouble();

		System.out.println("Champion 2 Mastery Point");
		double champion2_masteryPoint = TextIO.getlnDouble();
		System.out.println("Champion 2 Mastery Level");
		double champion2_masteryLevel = TextIO.getlnDouble();
		System.out.println("Number of Games played on champion 2");
		double champion2_gamesPlayed = TextIO.getlnDouble();

		/*
		 * 
		 * Now I have all the constants so the next section
		 * will be the calculation
		 * 
		 */

		while(champion1_masteryLevel > 0 && champion2_masteryLevel > 0 && champion1_gamesPlayed > 0 && champion2_gamesPlayed > 0) {

			double score1 = (champion1_masteryLevel * Math.log1p(champion1_gamesPlayed) * Math.log1p(champion1_masteryPoint));
			double score2 = (champion2_masteryLevel * Math.log1p(champion2_gamesPlayed) * Math.log1p(champion2_masteryPoint));

			double total = score1 + score2;
			double randomValue = (Math.random() * total);

			System.out.print("The odds of " + summoner1 + " winning is: ");
			System.out.println((score1/total)*100 + "%.");
			System.out.print("The odds of " + summoner2 + " winning is: ");
			System.out.println((score2/total)*100 + "%.");

			if (randomValue < score1) {
				System.out.println("The dice rolled: " + randomValue);
				System.out.println("The winner is: " + summoner1);
				TextIO.putln(summoner1 + " W | " + summoner2 + " L");
			} else if (randomValue > score1) {
				System.out.println("The dice rolled: " + randomValue);
				System.out.println("The winner is: " + summoner2);
				TextIO.putln(summoner2 + " W | " + summoner1 + " L");
			} else {
				System.out.println("The chances of this happening is almost non-existant, how did you two even tie? Settle this in an actual game.");
			}
			
			break;
		}

		if(champion1_masteryPoint == 0 || champion1_gamesPlayed == 0)
			System.out.println(summoner2 + " wins by default. " + summoner1 + " has no games played on this champion since the start of the mastery point system.");
		if(champion2_masteryPoint == 0 || champion2_gamesPlayed == 0)
			System.out.println(summoner1 + " wins by default. " + summoner2 + " has no games played on this champion since the start of the mastery point system.");
		
		// These are cases in which point = 0 .
		
		
		
		
	}

}
